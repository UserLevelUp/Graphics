"""Technical checks of the encoded zero-index tour against its declared scenes.

defines: graph.riemann.zero_index.media_review
Requires NumPy, Pillow and imageio-ffmpeg; no mpmath or app automation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from animate import Renderer

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def metrics(actual, expected):
    difference = np.abs(actual.astype(np.int16) - expected.astype(np.int16))
    return dict(meanAbsolute=float(difference.mean()),
                percentile99=float(np.percentile(difference, 99)),
                fractionOver40=float(np.mean(difference > 40)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--decoded-dir', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
    assert manifest['video']['sha256'] == sha(args.video), 'Encoded video hash differs from manifest.'
    assert (manifest['fps'], manifest['width'], manifest['height'], manifest['frames'], manifest['durationSeconds']) == (24,1280,720,2016,84)
    assert args.video.name == manifest['video']['path']
    assert args.video.stat().st_size == manifest['video']['bytes']
    for item in manifest['inputs']:
        assert sha(Path(item['path'])) == item['sha256'], item['path']
    prime_indices = [n for n in range(1,101) if is_prime(n)]
    controls = [1,4,6,8,9,10]
    assert manifest['primeIndices'] == prime_indices and len(prime_indices) == 25
    assert manifest['controlIndices'] == controls
    assert 'zero index' in manifest['meaning'].lower() and 'not individual primes' in manifest['meaning'].lower()
    expected_scenes = [('intro',None,12)] + [('prime',n,2) for n in prime_indices]
    expected_scenes += [('control',n,2) for n in controls] + [('summary',None,10)]
    assert len(manifest['scenes']) == len(expected_scenes) == 33
    cursor = 0
    targets = {}
    scene_records = []
    for scene, (kind,index,seconds) in zip(manifest['scenes'], expected_scenes):
        assert (scene['kind'],scene['index'],scene['seconds']) == (kind,index,seconds)
        assert scene['startFrame'] == cursor
        cursor += seconds*24
        assert scene['endFrameExclusive'] == cursor
        for number in (scene['startFrame'], cursor-1):
            targets[number] = scene
        if kind == 'intro' or index in (2,3,8,97):
            targets[scene['startFrame'] + (seconds*24)//2] = scene
        scene_records.append(dict(kind=kind,index=index,startFrame=scene['startFrame'],endFrameExclusive=cursor))
    assert cursor == 2016

    grids_file = next(Path(item['path']) for item in manifest['inputs'] if Path(item['path']).name == 'grids.json')
    renderer = Renderer(grids_file.parent)
    assert sorted(renderer.rows) == list(range(1,101))
    for n,row in renderer.rows.items():
        assert row['isPrimeIndex'] == is_prime(n)
    for n in prime_indices+controls:
        assert renderer.grids[f'Z{n}']['zeroIndex'] == n
        assert abs(renderer.grids[f'Z{n}']['centerT'] - float(renderer.rows[n]['height'])) < 1e-12
    sign_counts = {kind:{'down':0,'up':0} for kind in ('prime','composite','neither')}
    for row in renderer.rows.values():
        slope = float(row['slope'])
        assert slope != 0
        sign_counts[row['classificationPrimeIndex']]['down' if slope < 0 else 'up'] += 1
    assert sign_counts == {'prime':{'down':14,'up':11},'composite':{'down':35,'up':39},'neither':{'down':1,'up':0}}

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    probe = subprocess.run([ffmpeg,'-hide_banner','-i',str(args.video)],capture_output=True,text=True,encoding='utf-8',errors='replace')
    stream_lines = [line.strip() for line in probe.stderr.splitlines() if re.match(r'\s*Stream #\d+:\d+',line)]
    video_streams = [line for line in stream_lines if 'Video:' in line]
    audio_streams = [line for line in stream_lines if 'Audio:' in line]
    assert len(video_streams) == 1 and not audio_streams, stream_lines
    assert 'h264' in video_streams[0] and '1280x720' in video_streams[0]
    duration_match = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)',probe.stderr)
    assert duration_match
    hh,mm,ss = map(float,duration_match.groups())
    assert abs(hh*3600+mm*60+ss-84) <= 0.01

    reader = imageio_ffmpeg.read_frames(str(args.video),pix_fmt='rgb24',input_params=['-err_detect','explode'])
    meta = next(reader)
    assert tuple(meta['size']) == (1280,720)
    assert abs(meta['fps']-24)<1e-9 and abs(meta['duration']-84)<0.01
    args.decoded_dir.mkdir(parents=True,exist_ok=True)
    sample_frames = {0,287,288,335,1440,1487,1632,1679,1776,2015}
    compared = []
    decoded = []
    count = 0
    title_font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',30)
    for number,frame_bytes in enumerate(reader):
        actual = np.frombuffer(frame_bytes,dtype=np.uint8).reshape(720,1280,3)
        count += 1
        if number in targets:
            scene = targets[number]
            progress = (number-scene['startFrame'])/(scene['endFrameExclusive']-scene['startFrame']-1)
            kind,index = scene['kind'],scene['index']
            if kind == 'intro':
                expected_image = renderer.intro(progress)
            elif kind == 'summary':
                expected_image = renderer.summary()
            else:
                group = controls if kind == 'control' else prime_indices
                expected_image = renderer.local(index,progress,group.index(index)+1,len(group),kind=='control')
            comparison = metrics(actual,np.asarray(expected_image))
            # H264/yuv420p is lossy, especially at saturated edges. Full-frame and
            # title tolerances allow compression but reject mismatched scenes.
            assert comparison['meanAbsolute'] <= 3.5, (number,comparison)
            assert comparison['percentile99'] <= 35, (number,comparison)
            assert comparison['fractionOver40'] <= 0.01, (number,comparison)
            title_comparison = None
            if kind in ('prime','control'):
                # Independently construct the required ordinal/title, rather
                # than trusting the renderer's scene-to-index mapping.
                title = f'ZERO #{index}  •  '+('NONPRIME INDEX CONTROL' if kind=='control' else 'PRIME INDEX COMPARISON')
                plate = Image.new('RGB',(1280,100),(13,18,30))
                ImageDraw.Draw(plate).text((34,20),title,font=title_font,fill=(238,244,252))
                expected_title = np.asarray(plate)[15:61,28:1250]
                title_comparison = metrics(actual[15:61,28:1250],expected_title)
                assert title_comparison['meanAbsolute'] <= 3.5, (number,title_comparison)
                assert title_comparison['percentile99'] <= 35, (number,title_comparison)
            compared.append(dict(frame=number,kind=kind,zeroIndex=index,progress=progress,
                                 fullFrame=comparison,independentTitle=title_comparison))
        if number in sample_frames:
            dest = args.decoded_dir/f'frame-{number:04d}.png'
            Image.fromarray(actual).save(dest)
            decoded.append(dict(frame=number,path=str(dest.resolve()),sha256=sha(dest)))
        if count % 480 == 0:
            print(f'Decoded {count} frames; compared {len(compared)} scheduled samples.',flush=True)
    assert count == 2016 and len(compared) == len(targets) == 71
    assert len(decoded) == len(sample_frames)
    # Bind inputs again to detect concurrent changes during decoding.
    assert sha(args.video) == manifest['video']['sha256']
    for item in manifest['inputs']:
        assert sha(Path(item['path'])) == item['sha256'], item['path']
    inputs = [Path(__file__),args.manifest,args.video] + [Path(item['path']) for item in manifest['inputs']]
    report = dict(traceId='graph.riemann.zero_index.media_review',status='passed',
        reviewedAtUtc=datetime.now(timezone.utc).isoformat(),
        video=dict(path=str(args.video.resolve()),sha256=sha(args.video),bytes=args.video.stat().st_size,
                   width=1280,height=720,fps=24,frames=count,durationSeconds=84,codec=meta['codec'],audioStreams=0),
        coverage=dict(fullDecode=True,sceneCount=33,sceneBoundaryComparisons=66,
                      additionalMotionComparisons=5,
                      independentOrdinalTitleComparisons=sum(v['independentTitle'] is not None for v in compared),
                      extractedFrames=len(decoded),primeIndices=prime_indices,controlIndices=controls),
        meanings=dict(index='The ordinal of a known nontrivial zeta zero, not the value of an individual prime.',
                      starts='Known zeros on sigma=1/2 are supplied inputs, not a proof of RH.',
                      slopeResult='The sign of the starting slope does not separate prime indices from composite indices.',
                      signCounts=sign_counts),
        tolerances=dict(fullFrameMeanAbsolute=3.5,fullFramePercentile99=35,fractionOver40=0.01,
                        independentTitleMeanAbsolute=3.5,independentTitlePercentile99=35),
        maxObserved=dict(meanAbsolute=max(v['fullFrame']['meanAbsolute'] for v in compared),
                         percentile99=max(v['fullFrame']['percentile99'] for v in compared),
                         fractionOver40=max(v['fullFrame']['fractionOver40'] for v in compared)),
        scenes=scene_records,frameComparisons=compared,decodedFrames=decoded,
        streamDescriptions=stream_lines,
        inputs=[dict(path=str(p.resolve()),sha256=sha(p)) for p in inputs],
        limits=['Pixel comparisons verify the encoded video against the current checked renderer and independent ordinal titles.',
                'This is technical media QA, not a new validation of the zeta continuation mathematics.',
                'No UI or browser actions were performed; visual editorial review is separate.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status='passed',coverage=report['coverage'],maxObserved=report['maxObserved']),indent=2))


if __name__ == '__main__':
    main()
