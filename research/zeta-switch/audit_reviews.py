"""Audit recorded Watch review protocol; this does not accept reviewer conclusions.

python -B research/zeta-switch/audit_reviews.py
Only evidence/review-audit.json is written. Recur dispatch and protocol checks are read-only.
"""
# defines: graph.riemann.switch.review.audit
# consumes: graph.riemann.switch.carbon.response
# consumes: graph.riemann.switch.codex.response
# consumes: graph.riemann.switch.copilot.response
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

PROVIDERS = ('carbon', 'codex', 'copilot')
TRACE = 'graph.riemann.switch'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def instant(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError('Timestamp lacks an explicit timezone: ' + value)
    return result.astimezone(timezone.utc)


def one_line(text, key):
    values = re.findall(r'^' + re.escape(key) + r':[ \t]*(\S+)[ \t]*$', text, re.M)
    if len(values) != 1:
        raise ValueError('Expected exactly one ' + key + ' line')
    return values[0]


def verdict(text):
    values = re.findall(r'^VERDICT[ \t]*:?[ \t]*\r?\n?\s*(ACCEPT|REVISE)\b', text, re.M)
    if len(values) != 1:
        raise ValueError('Expected exactly one explicit ACCEPT or REVISE verdict')
    return values[0]


def audit_turn(events, text, prompt, expected_status, decision=None, previous_wait=None):
    checks = {}
    def check(name, value):
        checks[name] = bool(value)
    def event(state):
        matches = [item for item in events if item['state'] == state]
        if len(matches) != 1:
            raise ValueError('Expected one event ' + state)
        return matches[0]
    queued, running, delivered, ack = map(event, (
        'steering_queued', 'running', 'steering_delivered', 'steering_acknowledged'))
    start = instant(running['started_at'])
    deadline = instant(queued['deadline_utc'])
    acknowledged = instant(ack['at'])
    clock_text = one_line(text, 'CLOCK')
    clock = instant(clock_text)
    token = queued['token']
    status = one_line(text, 'STATUS')
    check('eventOrder', instant(queued['at']) <= start <= instant(running['at'])
          <= instant(delivered['at']) <= acknowledged)
    check('deadlineIs180SecondsFromQueue', abs((deadline - instant(queued['at'])).total_seconds() - 180) < 0.1)
    check('sameDeliveredDeadline', delivered['deadline_utc'] == queued['deadline_utc'])
    check('ackBeforeAbsoluteDeadline', acknowledged <= deadline)
    check('ackWithin180SecondsOfStart', 0 <= (acknowledged - start).total_seconds() <= 180)
    check('reportedClockWithinTurn', start <= clock <= acknowledged)
    check('matchingTokens', one_line(text, 'ACK') == token == delivered['token'] == ack['token'])
    check('matchingStatus', status == expected_status == ack['worker_status'])
    check('deadlinePresentInPrompt', 'Absolute UTC progress deadline: ' + queued['deadline_utc'] in prompt)
    check('tokenPresentInPrompt', 'acknowledgement token ' + token + '.' in prompt)
    check('budgetPresentInPrompt', 'Budget 180 seconds.' in prompt)
    if expected_status == 'CHECKPOINT':
        check('checkpointSections', all(section in text.upper() for section in ('FINDINGS', 'UNCERTAINTY', 'NEXT')))
    else:
        check('finalSections', all(section in text.upper() for section in ('VERDICT', 'REASONING', 'TESTS')))
    if decision is None:
        check('initialToken', token == 'initial')
    else:
        check('continuationToken', token != 'initial' and decision['token'] == token)
        check('continuationAuthorization', decision['action'] in ('continue', 'steer')
              and decision['run_id'] == queued['run_id'] and decision['after_turn'] == queued['turn'] - 1)
        check('handoffBeforeContinuation', instant(previous_wait['at']) <= instant(decision['queued_at']) <= instant(queued['at']))
    return {
        'turn': queued['turn'], 'responseStatus': status, 'acknowledgedToken': token,
        'startedAt': running['started_at'], 'deadlineUtc': queued['deadline_utc'],
        'acknowledgedAt': ack['at'], 'elapsedSeconds': (acknowledged - start).total_seconds(),
        'reportedClock': clock_text, 'reportedClockUtc': clock.isoformat(),
        'clockExecutionEvidence': 'provider-reported only; a timestamp does not prove a clock command executed',
        'checks': checks, 'passed': all(checks.values())}


def command(argv, cwd):
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, encoding='utf-8', errors='replace', timeout=45)
    return {'argv': list(map(str, argv)), 'cwd': str(cwd), 'exitCode': completed.returncode,
            'stdout': completed.stdout, 'stderr': completed.stderr,
            'stdoutSha256': hashlib.sha256(completed.stdout.encode('utf-8')).hexdigest()}


def artifact(path, root, text=False):
    raw_path = str(path)
    if raw_path.startswith(chr(92) * 2 + '?' + chr(92)):
        raw_path = raw_path[4:]
    actual = Path(raw_path).resolve()
    if not actual.is_relative_to(root):
        raise ValueError('Recorded artifact lies outside project: ' + str(path))
    record = {'path': actual.relative_to(root).as_posix(), 'sha256': sha(actual)}
    if text:
        record['text'] = actual.read_text(encoding='utf-8-sig')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    base = root / 'research/zeta-switch'
    output = args.output or base / 'evidence/review-audit.json'
    issues, reviews, commands = [], [], []
    for provider in PROVIDERS:
        try:
            index = read_json(base / provider / 'latest-run.json')
            run = (base / provider / 'runs' / index['run_id']).resolve()
            if not run.is_relative_to(base / provider / 'runs') or index['provider'] != provider:
                raise ValueError('Invalid latest-run index')
            events = [json.loads(line) for line in (run / 'events.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
            if not events or any(e['provider'] != provider or e['run_id'] != index['run_id']
                                 or e['trace_id'] != TRACE + '.' + provider + '.progress' for e in events):
                raise ValueError('Event identity mismatch')
            if any(instant(a['at']) > instant(b['at']) for a, b in zip(events, events[1:])):
                raise ValueError('Event timestamps are not monotone')
            status = read_json(run / 'status.json')
            if status != events[-1] or status['state'] != 'complete':
                raise ValueError('Final status is not the recorded complete event')
            turns = sorted(set(e['turn'] for e in events))
            if turns != list(range(1, len(turns) + 1)) or len(turns) < 2:
                raise ValueError('Missing checkpoint-to-final turn sequence')
            audited_turns = []
            for turn in turns:
                turn_dir = run / ('turn-%02d' % turn)
                text = (turn_dir / 'stdout.txt').read_text(encoding='utf-8-sig')
                prompt = (turn_dir / 'prompt.txt').read_text(encoding='utf-8-sig')
                decision = read_json(run / ('steering-after-%02d.json' % (turn - 1))) if turn > 1 else None
                waits = [e for e in events if e['turn'] == turn - 1 and e['state'] == 'awaiting_coordinator']
                if turn > 1 and len(waits) != 1:
                    raise ValueError('Missing unique coordinator handoff')
                checked = audit_turn([e for e in events if e['turn'] == turn], text, prompt,
                                     'COMPLETE' if turn == turns[-1] else 'CHECKPOINT', decision,
                                     waits[0] if waits else None)
                checked['response'] = artifact(turn_dir / 'stdout.txt', root)
                checked['prompt'] = artifact(turn_dir / 'prompt.txt', root)
                if decision is not None:
                    checked['steering'] = artifact(run / ('steering-after-%02d.json' % (turn - 1)), root)
                if not checked['passed']:
                    issues.extend(provider + ' turn ' + str(turn) + ': ' + k for k, v in checked['checks'].items() if not v)
                audited_turns.append(checked)
            report = (run / 'review.md').read_text(encoding='utf-8-sig')
            if report != (base / provider / 'review.md').read_text(encoding='utf-8-sig'):
                raise ValueError('Published review differs from the run report')
            final_response = (run / ('turn-%02d' % turns[-1]) / 'stdout.txt').read_text(encoding='utf-8-sig')
            if report != 'publish: ' + TRACE + '.' + provider + '.response\n\n' + final_response:
                raise ValueError('Final review does not preserve the final response')
            review_verdict = verdict(report)
            checked_command = command([sys.executable, '-B', str(base / 'verify-review.py'), provider], root)
            commands.append(checked_command)
            if checked_command['exitCode'] != 0:
                issues.append(provider + ': configured protocol verifier failed')
            reviews.append({'provider': provider, 'runId': index['run_id'], 'finalState': status['state'],
                            'verdict': review_verdict, 'verdictMeaning': 'review of supplied mathematical contract and validation plan only',
                            'report': artifact(run / 'review.md', root, text=True),
                            'events': artifact(run / 'events.jsonl', root), 'turns': audited_turns,
                            'configuredProtocolCheckPassed': checked_command['exitCode'] == 0})
        except (ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
            issues.append(provider + ': ' + str(error))
    attempts = []
    dispatch = command(['recur', 'warp', 'dispatch', TRACE, '-d', str(root), '--json'], root)
    raw_stdout = dispatch.pop('stdout')
    dispatch['stdoutCapture'] = 'parsed and compacted into dispatchAttempts; complete raw stdout SHA-256 retained'
    commands.append(dispatch)
    if dispatch['exitCode'] != 0:
        issues.append('Recur dispatch inspection failed')
        dispatch['stdout'] = raw_stdout
    else:
        view = json.loads(raw_stdout)
        if view.get('warp_id') != TRACE:
            issues.append('Dispatch output has wrong scope')
        for attempt in view.get('attempts', []):
            row = {key: attempt.get(key) for key in ('warp_id', 'slice_id', 'attempt', 'state', 'claimed_at_unix',
                'finished_at_unix', 'elapsed_seconds', 'host_id', 'test_failures', 'input_fingerprints', 'verification_inputs')}
            row['agentResult'] = attempt.get('agent_result')
            row['testResults'] = []
            for result in attempt.get('test_results', []):
                captured = dict(result)
                captured['stdoutArtifact'] = artifact(result['stdout'], root, text=True)
                captured['stderrArtifact'] = artifact(result['stderr'], root, text=True)
                row['testResults'].append(captured)
            agent = attempt.get('agent_result', {})
            if agent.get('stdout'):
                actual = artifact(agent['stdout'], root, text=True)
                raw_agent = actual.pop('text')
                row['agentStdoutArtifact'] = actual
                row['observedRunIdsInAgentOutput'] = sorted(set(re.findall(r'"run_id":\s*"([^"]+)"', raw_agent)))
            attempts.append(row)
        for review in reviews:
            rows = [a for a in attempts if a['slice_id'] == review['provider']]
            if not rows:
                issues.append(review['provider'] + ': no scoped dispatch attempt')
                continue
            latest = max(rows, key=lambda a: a['attempt'])
            review['dispatchAttempt'] = latest['attempt']
            good = latest['state'] == 'produced' and latest['testResults'] and all(
                r.get('success') and r.get('exit_code') == 0 and not r.get('timed_out') for r in latest['testResults'])
            if not good:
                issues.append(review['provider'] + ': latest attempt lacks produced state with successful tests')
            if review['runId'] not in latest.get('observedRunIdsInAgentOutput', []):
                issues.append(review['provider'] + ': dispatch stdout does not link to audited run')
    if len(reviews) != len(PROVIDERS):
        issues.append('Not all three provider runs were audited')
    result = {
        'schema': 'graph-watch-review-audit-v2', 'traceId': TRACE + '.review.audit',
        'auditedAtUtc': datetime.now(timezone.utc).isoformat(),
        'status': 'passed' if not issues else 'failed', 'issues': issues,
        'statusMeaning': 'recorded protocol, ACK, timestamp, artifact, and configured-check audit only',
        'runner': artifact(base / 'run-review.py', root),
        'reviews': reviews, 'dispatchAttempts': attempts, 'commands': commands,
        'providerVerdicts': {r['provider']: r['verdict'] for r in reviews},
        'providersRequestingRevision': [r['provider'] for r in reviews if r['verdict'] == 'REVISE'],
        'coordinatorAcceptance': 'not decided by this audit; any resolution must be recorded separately',
        'limits': [
            'Clock command execution is provider-reported. A plausible CLOCK timestamp does not prove execution.',
            'Elapsed response time is derived from recorded runner start/ACK events, not independently attested wall-clock instrumentation.',
            'Produced means configured protocol checks succeeded, not that a reviewer accepted the plan or that mathematics/code/tests are certified.',
            'Each reviewer verdict is preserved verbatim in its report; REVISE is never converted to ACCEPT by this audit.',
            'Compact attempt records retain actual configured test results and stdout/stderr artifact hashes and text.',
            'These reviews and this audit do not establish the Riemann Hypothesis.']}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'reviews': len(reviews), 'attempts': len(attempts),
                      'verdicts': result['providerVerdicts'], 'issues': issues, 'output': str(output)}))
    return 0 if not issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
