/* defines: graph.riemann.continuation.presentation.aftereffects
   Preparation only: root executes after accepting the scientific animation.
   CONFIG.output, CONFIG.story, optional CONFIG.voice[sceneId] and CONFIG.animationVideo.
   Output: presentation.aep, queued presentation.mp4, build-status.txt. No render starts here. */
(function () {
    app.beginSuppressDialogs();
    var statusFile = new File(CONFIG.output + "/build-status.txt");
    function report(value) { statusFile.open("w"); statusFile.encoding="UTF-8"; statusFile.write(value); statusFile.close(); }
    function normalize(file) { return file.fsName.replace(/\\/g,"/").toLowerCase(); }
    var saved = new File(CONFIG.output + "/presentation.aep");
    try {
        var story=CONFIG.story;
        if(CONFIG.acceptedAnimation !== true || !story || !story.productionGate || !story.productionGate.readyForProduction || story.productionGate.resultSceneMustBeFinalized)
            throw Error("Presentation production is blocked until animation acceptance and result finalization.");
        if(story.scenes.length!==9 || story.durationSeconds!==138 || story.narrationWordCount>310)
            throw Error("Expected nine finalized scenes, 138 seconds, and at most 310 spoken words.");
        for(var si=0;si<story.scenes.length;si++)
            if(story.scenes[si].finalizationRequired) throw Error("Unfinalized scene: "+story.scenes[si].id);
        if(!story.resultSummary || !story.resultSummary.branches || story.resultSummary.branches.length!==3)
            throw Error("Missing independently checked three-branch result summary.");
        if(!CONFIG.animationData || !CONFIG.animationData.trajectories || CONFIG.animationData.trajectories.length!==3)
            throw Error("Missing accepted native trajectory metadata.");
        for(var bi=0;bi<story.resultSummary.branches.length;bi++) {
            var expected=story.resultSummary.branches[bi],matched=false;
            for(var bj=0;bj<CONFIG.animationData.trajectories.length;bj++) {
                var nativeBranch=CONFIG.animationData.trajectories[bj];
                if(nativeBranch.id===expected.id) {matched=true;if(nativeBranch.status!==expected.status)throw Error("Native/reference branch-status mismatch: "+expected.id);}
            }
            if(!matched)throw Error("Missing native branch: "+expected.id);
        }
        var scientificFile=new File(CONFIG.animationVideo || CONFIG.output+"/../animation/scientific-animation.mp4");
        if(!scientificFile.exists) throw Error("Accepted scientific video is missing: "+scientificFile.fsName);
        // Do not discard an unrelated saved project or any unsaved partial project.
        if(app.project && (app.project.numItems>0 || app.project.file)) {
            var samePresentation=app.project.file && normalize(app.project.file)===normalize(saved);
            var animationProject=new File(scientificFile.fsName.replace(/\.mp4$/i,".aep"));
            var siblingOutputs=normalize(animationProject.parent.parent)===normalize(new Folder(CONFIG.output).parent);
            var sameAcceptedAnimation=app.project.file && siblingOutputs && normalize(app.project.file)===normalize(animationProject);
            if(!samePresentation && (!sameAcceptedAnimation || app.project.dirty))
                throw Error("Refusing to replace an unrelated, unsaved, or modified accepted-animation project. Close it explicitly first.");
            app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
        }
        // Reuse an existing empty project: app.newProject() can prompt even for an empty project.
        if(!app.project) app.newProject();
        var master=app.project.items.addComp("Continuation presentation",1920,1080,1,story.durationSeconds,24);
        var C={bg:[.035,.052,.09],card:[.064,.09,.145],edge:[.16,.24,.33],ink:[.94,.96,1],muted:[.65,.75,.85],
            cyan:[.36,.91,.94],amber:[1,.77,.33],violet:[.72,.56,.9],white:[1,1,1],face:[.98,.96,.88]};
        var branchColors=[[1,.88,.40],[.44,.94,1],[1,.59,.86]];
        var phaseColors=[[27/255,115/255,94/255],[136/255,102/255,39/255],[101/255,60/255,133/255],[39/255,77/255,136/255]];
        var notes=[],voiceRecords=[];
        master.bgColor=C.bg;
        function transform(layer,property) { return layer.property("ADBE Transform Group").property(property); }
        function fillStroke(root,fill,stroke,width) {
            if(fill) {var f=root.addProperty("ADBE Vector Graphic - Fill");f.property("ADBE Vector Fill Color").setValue(fill);}
            if(stroke && width) {var s=root.addProperty("ADBE Vector Graphic - Stroke");s.property("ADBE Vector Stroke Color").setValue(stroke);s.property("ADBE Vector Stroke Width").setValue(width);}
        }
        function rect(c,name,x,y,w,h,fill,stroke,width,radius) {
            var l=c.layers.addShape();l.name=name;
            var root=l.property("ADBE Root Vectors Group"),r=root.addProperty("ADBE Vector Shape - Rect");
            r.property("ADBE Vector Rect Size").setValue([w,h]);
            r.property("ADBE Vector Rect Roundness").setValue(radius===undefined?18:radius);
            fillStroke(root,fill,stroke,width);transform(l,"ADBE Position").setValue([x+w/2,y+h/2]);return l;
        }
        function ellipse(c,name,x,y,w,h,fill,stroke,width) {
            var l=c.layers.addShape();l.name=name;
            var root=l.property("ADBE Root Vectors Group"),e=root.addProperty("ADBE Vector Shape - Ellipse");
            e.property("ADBE Vector Ellipse Size").setValue([w,h]);fillStroke(root,fill,stroke,width);
            transform(l,"ADBE Position").setValue([x,y]);return l;
        }
        function poly(c,name,vertices,color,width,closed,fill) {
            var l=c.layers.addShape();l.name=name;transform(l,"ADBE Position").setValue([0,0]);
            var root=l.property("ADBE Root Vectors Group"),path=root.addProperty("ADBE Vector Shape - Group"),s=new Shape(),z=[];
            for(var i=0;i<vertices.length;i++)z.push([0,0]);
            s.vertices=vertices;s.inTangents=z;s.outTangents=z;s.closed=!!closed;
            path.property("ADBE Vector Shape").setValue(s);fillStroke(root,fill,color,width);return l;
        }
        function line(c,name,x1,y1,x2,y2,color,width) {return poly(c,name,[[x1,y1],[x2,y2]],color,width,false,null);}
        function arrow(c,name,x1,y1,x2,y2,color,width) {
            var stem=line(c,name+" stem",x1,y1,x2,y2,color,width||4),a=Math.atan2(y2-y1,x2-x1),r=15;
            poly(c,name+" tip",[[x2,y2],[x2-r*Math.cos(a-.5),y2-r*Math.sin(a-.5)],[x2-r*Math.cos(a+.5),y2-r*Math.sin(a+.5)]],null,0,true,color);
            return stem;
        }
        function text(c,name,value,x,y,size,color,w,h) {
            var l=w?c.layers.addBoxText([w,h||180]):c.layers.addText(value);l.name=name;
            var p=l.property("ADBE Text Properties").property("ADBE Text Document"),d=p.value;
            d.text=value;d.font="SegoeUI";d.fontSize=size;d.fillColor=color||C.ink;d.applyStroke=false;
            d.autoLeading=false;d.leading=size*1.22;d.justification=ParagraphJustification.LEFT_JUSTIFY;p.setValue(d);
            var b=l.sourceRectAtTime(0,false);transform(l,"ADBE Anchor Point").setValue([b.left,b.top]);
            transform(l,"ADBE Position").setValue([x,y]);return l;
        }
        function wrap(value,columns) {
            var words=value.split(/\s+/),lines=[],current="";
            for(var i=0;i<words.length;i++) {
                if(current && current.length+1+words[i].length>columns){lines.push(current);current=words[i];}
                else current+=(current?" ":"")+words[i];
            }
            if(current)lines.push(current);return lines.join("\r");
        }
        function appear(layer,at,until) {layer.inPoint=at;if(until!==undefined)layer.outPoint=until;}
        function local(layer,parent,position) {layer.parent=parent;transform(layer,"ADBE Position").setValue(position);return layer;}
        function presenter(c,duration) {
            rect(c,"Compass quiet backing",85,695,245,305,[.045,.075,.12],null,0,85);
            var rig=c.layers.addNull();rig.name="Compass editable character rig";transform(rig,"ADBE Position").setValue([205,865]);
            var bob=transform(rig,"ADBE Position");bob.setValueAtTime(0,[205,865]);bob.setValueAtTime(duration*.4,[205,859]);bob.setValueAtTime(duration,[205,865]);
            local(rect(c,"Compass body",-68,-3,136,125,[.09,.18,.27],C.cyan,3,34),rig,[0,59.5]);
            local(ellipse(c,"Compass face",0,-88,116,116,C.face,C.edge,3),rig,[0,-88]);
            local(ellipse(c,"Compass left eye",-19,-93,8,11,C.bg,null,0),rig,[-19,-93]);
            local(ellipse(c,"Compass right eye",19,-93,8,11,C.bg,null,0),rig,[19,-93]);
            local(poly(c,"Compass smile",[[-16,-66],[0,-60],[16,-66]],C.edge,3,false,null),rig,[0,0]);
            local(rect(c,"Compass left foot",-56,143,45,13,C.cyan,null,0,6),rig,[-33.5,129.5]);
            local(rect(c,"Compass right foot",11,143,45,13,C.cyan,null,0,6),rig,[33.5,129.5]);
            var arm=c.layers.addNull();arm.name="Compass pointing arm rig";local(arm,rig,[56,25]);
            local(poly(c,"Compass pointing sleeve",[[0,0],[65,-20],[108,-54]],C.cyan,15,false,null),arm,[0,0]);
            local(ellipse(c,"Compass wrist",108,-54,17,17,C.amber,null,0),arm,[108,-54]);
            local(poly(c,"Compass original pointer hand",[[111,-60],[148,-67],[122,-43]],null,0,true,C.cyan),arm,[0,0]);
            var rotation=transform(arm,"ADBE Rotate Z");rotation.setValueAtTime(0,5);rotation.setValueAtTime(duration*.35,-4);rotation.setValueAtTime(duration*.7,1);rotation.setValueAtTime(duration,-2);
            text(c,"Compass name","COMPASS",130,1020,22,C.muted);
        }
        function bubbles(c,scene) {
            rect(c,"Speech bubble editable",70,440,355,205,[.10,.16,.23],C.cyan,2,24);
            poly(c,"Speech bubble tail",[[188,645],[226,645],[207,700]],C.cyan,2,true,[.10,.16,.23]);
            for(var i=0;i<scene.bubbles.length;i++) {
                var t=text(c,"Bubble "+(i+1),wrap(scene.bubbles[i],21),95,472,34,C.ink,307,160);
                appear(t,scene.durationSeconds*i/scene.bubbles.length,scene.durationSeconds*(i+1)/scene.bubbles.length);
            }
        }
        function baseScene(scene,index) {
            var c=app.project.items.addComp((index+1)+" • "+scene.title,1920,1080,1,scene.durationSeconds,24);c.bgColor=C.bg;
            rect(c,"Full background",0,0,1920,1080,C.bg,null,0,0);
            rect(c,"Scientific visual backing",495,215,1345,770,C.card,C.edge,1,26);
            text(c,"Scene title",scene.title,80,55,52,C.ink,1710,130);
            text(c,"Scene progress",("0"+(index+1)).slice(-2)+" / "+("0"+story.scenes.length).slice(-2),1680,166,24,C.cyan);
            presenter(c,scene.durationSeconds);bubbles(c,scene);
            return c;
        }
        function scopeScene(c) {
            rect(c,"Coordinator scope",565,278,1190,570,[.075,.11,.18],C.edge,2,26);
            text(c,"Coordinator heading","COORDINATOR",620,312,28,C.cyan);
            text(c,"Coordinator question","One question. Recorded evidence.",620,358,41,C.ink,1060,80);
            line(c,"Scope branch stem",1160,427,1160,475,C.muted,3);
            line(c,"Scope branch rail",850,475,1485,475,C.muted,3);
            line(c,"Science child connection",850,475,850,510,C.muted,3);
            line(c,"Presentation child connection",1485,475,1485,510,C.muted,3);
            rect(c,"Scientific animation scope",615,510,470,230,[.06,.17,.22],C.cyan,2,20);
            rect(c,"Presentation scope",1245,510,440,230,[.12,.12,.21],C.violet,2,20);
            text(c,"Science scope text","Scientific\ranimation",648,548,41,C.ink,400,120);
            text(c,"Science scope note","Compute • check • accept",648,685,28,C.muted);
            text(c,"Presentation scope text","Presentation",1280,555,41,C.ink,370,90);
            text(c,"Presentation scope note","Explain accepted evidence",1280,635,28,C.muted,350,80);
            arrow(c,"Acceptance gate",1098,625,1227,625,C.amber,4);
            text(c,"Gate label","accept\rfirst",1110,665,28,C.amber);
            text(c,"Scope limitation","A work boundary — not a mathematical force",620,790,31,C.muted);
        }
        function axes(c,name,x,y,w,h) {
            arrow(c,name+" real axis",x,y+h/2,x+w,y+h/2,C.muted,2);
            arrow(c,name+" imaginary axis",x+w/2,y+h,x+w/2,y,C.muted,2);
        }
        function originScene(c,scene) {
            text(c,"Family formula","Fₐ(s) = ζ(s) − a        a: 0 → 1",545,235,43,C.ink);
            rect(c,"Input diagram",545,330,570,450,[.045,.075,.12],C.edge,1,18);
            rect(c,"Output diagram",1180,330,590,450,[.045,.075,.12],C.edge,1,18);
            text(c,"Input heading","INPUT PLANE: s",575,358,30,C.cyan);
            text(c,"Output heading","OUTPUT PLANE: ζ(s)",1210,358,30,C.amber);
            axes(c,"Fixed input",600,440,450,260);
            text(c,"Fixed input note","The s-axes stay fixed",607,730,30,C.muted);
            var target=c.layers.addNull();target.name="Moving output origin rig";
            transform(target,"ADBE Position").setValueAtTime(1,[1335,570]);
            transform(target,"ADBE Position").setValueAtTime(scene.durationSeconds-2,[1600,570]);
            var blocks=[[0,-95],[-95,-95],[-95,0],[0,0]];
            for(var q=0;q<4;q++) {
                var tile=rect(c,"Local phase quadrant "+q,0,0,95,95,phaseColors[q],null,0,0);
                local(tile,target,[blocks[q][0]+47.5,blocks[q][1]+47.5]);
            }
            line(c,"Output real rail",1240,570,1710,570,C.muted,2);
            local(line(c,"Moving local horizontal",-115,0,115,0,C.ink,2),target,[0,0]);
            local(line(c,"Moving local vertical",0,-115,0,115,C.ink,2),target,[0,0]);
            local(ellipse(c,"Moving target a",0,0,17,17,C.amber,C.bg,2),target,[0,0]);
            text(c,"Output zero label","0",1325,700,32,C.ink);text(c,"Output one label","1",1590,700,32,C.ink);
            text(c,"Origin note","Four phase regions are centered on the moving output target.",580,830,32,C.muted,1160,90);
        }
        function trackingScene(c) {
            text(c,"Inverse derivative formula","ds/da = 1 / ζ′(s)",555,252,48,C.ink);
            text(c,"Local hypothesis","Local inverse: ζ′(s) ≠ 0",1190,264,32,C.amber);
            text(c,"Schematic label","SCHEMATIC: ONE PREDICTOR–CORRECTOR STEP",555,340,26,C.muted);
            poly(c,"Illustrative local curve",[[620,790],[760,690],[930,605],[1120,570],[1330,610],[1560,720]],C.muted,4,false,null);
            ellipse(c,"Current point",760,690,22,22,C.cyan,C.bg,2);
            arrow(c,"Derivative prediction",760,690,1115,505,C.cyan,5);
            ellipse(c,"Predicted point",1115,505,20,20,null,C.cyan,3);
            arrow(c,"Newton correction",1115,505,1120,570,C.amber,5);
            ellipse(c,"Corrected point",1120,570,22,22,C.amber,C.bg,2);
            text(c,"Current label","current",635,725,34,C.cyan);
            text(c,"Prediction label","prediction",1000,425,34,C.cyan);
            text(c,"Correction label","corrected sample",1190,540,34,C.amber);
            text(c,"Step rule","Shrink the target step when motion or correction grows.",555,855,32,C.ink,1200,85);
            text(c,"Step limit","A successful numerical step is not a certified continuation tube.",555,925,28,C.muted,1200,70);
        }
        function priorWorkScene(c) {
            text(c,"Prior-work family","TWO FIXED ORIGINS  →  ONE CONTINUOUS TARGET",550,245,31,C.ink);
            var xs=[550,1190,550,1190],ys=[330,330,630,630];
            var headings=["EARLIER PROJECT","WEGERT · 2010","LESTER · 2014","CLASSICAL METHODS"];
            var body=["ζ(s) and ζ(s) − 1\rNow move the target a.","Phase plots are the foundation.\rOur palette uses four bins.","Existing theory of ζ(s) = a.\rHere: three tracked paths.","Derivative prediction\r+ Newton correction"];
            var sources=["Checkpoint f24b64c","arXiv:1007.2295","arXiv:1402.0169","No new algorithm claimed"];
            var colors=[C.cyan,C.violet,C.amber,C.cyan];
            for(var i=0;i<4;i++) {
                rect(c,"Prior-work card "+i,xs[i],ys[i],590,245,[.045,.075,.12],colors[i],2,20);
                text(c,"Prior-work heading "+i,headings[i],xs[i]+26,ys[i]+25,31,colors[i]);
                text(c,"Prior-work reuse "+i,body[i],xs[i]+26,ys[i]+90,30,C.ink,540,98);
                text(c,"Prior-work credit "+i,sources[i],xs[i]+26,ys[i]+201,28,C.muted);
            }
            text(c,"Prior-work full credits","Full source links and precise reuse: sources.txt · checked 2026-11-15",550,925,28,C.muted,1240,75);
        }
        function priorResultsScene(c) {
            text(c,"Prior-results distinction","THREE DIFFERENT TYPES OF EVIDENCE ABOUT ZETA ZEROS",550,245,29,C.ink);
            var xs=[550,970,1390],cols=[C.cyan,C.amber,C.violet];
            for(var i=0;i<3;i++)rect(c,"Prior-result card "+i,xs[i],330,390,555,[.045,.075,.12],cols[i],2,20);
            text(c,"Finite-check authors","PLATT–TRUDGIAN",575,360,29,C.cyan,340,90);
            text(c,"Verified height","3 × 10¹²",575,450,57,C.ink);
            text(c,"Finite-check statement","Height checked using\rinterval arithmetic.",575,545,30,C.ink,335,115);
            text(c,"Finite-check scope","Our window adds no\rnew verified RH height.",575,675,28,C.muted,335,100);
            text(c,"Finite-check source","2020\rarXiv:2004.09765",575,790,28,C.muted,335,90);
            text(c,"Proportion author","LAMZOURI\r2026 PREPRINT",995,360,29,C.amber,340,90);
            text(c,"Proportion bound",">67.25%",995,475,55,C.ink);
            text(c,"Proportion scope","Simple + on the line.\rAsymptotic proportion.",995,570,28,C.ink,335,100);
            text(c,"Proportion context","Builds on Claude /\rAnthropic's argument.",995,690,28,C.muted,335,95);
            text(c,"Proportion clarification","Not a % of RH solved.",995,775,27,C.amber,340,40);
            text(c,"Proportion source","arXiv:2609.02882v2",995,830,28,C.muted,340,45);
            text(c,"OpenAI attribution","OPENAI\rREPORTED RESULT",1415,360,29,C.violet,340,90);
            text(c,"Zero-free region","Re(s) > 7/8",1415,475,43,C.ink,340,85);
            text(c,"Zero-free scope","Zero-free half-plane.\rLean formalization\rnot replayed here.",1415,580,29,C.ink,335,145);
            text(c,"OpenAI source","openai/math\rlean/docs/003.md",1415,790,28,C.muted,335,90);
            text(c,"Prior-results limit","None automatically certifies our moving nonzero targets. Sources checked 2026-11-15.",550,925,28,C.muted,1240,90);
        }
        var scientific=app.project.importFile(new ImportOptions(scientificFile));
        if(scientific.width!==1920 || scientific.height!==1080 || scientific.duration<28)
            throw Error("Unexpected accepted scientific video dimensions or duration.");
        var crop=app.project.items.addComp("Accepted scientific plot crop",1130,620,1,scientific.duration,24);
        var movie=crop.layers.add(scientific);movie.name="Accepted video: plot region only";movie.audioEnabled=false;
        transform(movie,"ADBE Position").setValue([scientific.width/2-150,scientific.height/2-235]);
        function resultScene(c,scene) {
            text(c,"Result scope","INDEPENDENTLY CHECKED FINITE PATHS",550,226,28,C.cyan);
            var plot=c.layers.add(crop);plot.name="Accepted scientific trajectory replay";plot.audioEnabled=false;
            transform(plot,"ADBE Position").setValue([555+1130/2,290+620/2]);plot.timeRemapEnabled=true;plot.outPoint=scene.durationSeconds;
            var fraction="Math.min(1,Math.max(0,(time-1)/"+(scene.durationSeconds-3)+"))";
            plot.property("ADBE Time Remapping").expression="2+26*("+fraction+")";
            rect(c,"Plot boundary",555,290,1130,620,null,C.muted,2,0);
            var sigmas=[.05,.5,1,2,3];
            for(var k=0;k<sigmas.length;k++) {
                var x=555+(sigmas[k]-.05)/2.95*1130;
                line(c,"Sigma tick "+k,x,910,x,920,C.muted,2);text(c,"Sigma value "+k,String(sigmas[k]),x-16,931,30,C.muted);
            }
            for(var t=10;t<=30;t+=5) text(c,"Height tick "+t,String(t),505,290+(30-t)/20*620-14,30,C.muted);
            text(c,"Height symbol","t",512,252,30,C.muted);
            text(c,"Sigma symbol","σ",1710,925,32,C.muted);
            var current=text(c,"Current target","a = 0.000",1460,226,36,C.ink);
            current.property("ADBE Text Properties").property("ADBE Text Document").expression="'a = '+("+fraction+").toFixed(3)";
            text(c,"Path legend","Solid: traversed samples. Dashed: later precomputed samples.",505,975,26,C.muted,1300,44);
            text(c,"Exit handling note","Held exit markers retain their earlier target; they are not current roots.",505,1013,26,C.muted,1300,44);
        }
        function methodsScene(c) {
            var names=["COLOR","CONTINUATION","HIGHER PRECISION","ANALYTIC BOUNDS"],
                descriptions=["See the phase around\rthe moving origin.","Follow a labeled solution;\rrecord exits and warnings.","Compare independent values,\rsmaller steps, and reversal.","Needed for a rigorous\rcontinuation certificate."],
                xs=[550,1195,550,1195],ys=[290,290,610,610];
            for(var i=0;i<4;i++) {
                var accent=i===0?C.violet:i===1?C.cyan:i===2?C.amber:C.muted;
                rect(c,"Method card "+i,xs[i],ys[i],590,245,[.045,.075,.12],accent,2,20);
                text(c,"Method heading "+i,names[i],xs[i]+28,ys[i]+28,31,accent);
                text(c,"Method meaning "+i,descriptions[i],xs[i]+28,ys[i]+97,32,C.ink,530,110);
                if(i===3) text(c,"Certificate state","NOT YET CERTIFIED",xs[i]+28,ys[i]+207,24,C.amber);
            }
            text(c,"Combination limit","Agreement is evidence. A certificate needs proved bounds.",550,925,34,C.ink,1210,70);
        }
        function confinementScene(c) {
            text(c,"Original finite prediction","ORIGINAL CLAIM: ALL THREE PATHS STAY INSIDE R",550,245,30,C.muted);
            var rows=story.resultSummary.branches;
            for(var j=0;j<rows.length;j++) {
                var row=rows[j],y=325+j*190,col=branchColors[j];
                rect(c,row.id+" outcome card",550,y,1235,158,[.045,.075,.12],C.edge,1,18);
                text(c,row.id+" identity",row.id,580,y+35,48,col);
                if(row.status==="exited") {
                    text(c,row.id+" exit","EXITED THE CHOSEN WINDOW",710,y+30,34,C.ink);
                    text(c,row.id+" exit target","σ = 3 at a ≈ "+Number(row.exitA).toFixed(6),710,y+88,32,C.muted);
                    arrow(c,row.id+" outward arrow",1550,y+79,1710,y+79,col,5);
                    line(c,row.id+" boundary",1650,y+25,1650,y+133,C.ink,2);
                } else if(row.status==="completed") {
                    text(c,row.id+" one point","REACHED A FINITE 1-POINT",710,y+30,34,C.ink);
                    text(c,row.id+" endpoint","s ≈ "+Number(row.endpoint.real).toFixed(6)+" + "+Number(row.endpoint.imaginary).toFixed(6)+" i",710,y+88,32,C.muted);
                    ellipse(c,row.id+" endpoint icon",1660,y+80,28,28,col,C.bg,2);
                } else throw Error("Unresolved branch cannot be narrated as a completed outcome: "+row.id);
            }
            text(c,"Finite conclusion","Numerical counterevidence to confinement; no RH conclusion.",550,925,32,C.amber,1230,70);
        }
        function globalScene(c) {
            text(c,"Global zero condition","ζ(ρ) = 0,   0 < Re ρ < 1\r⇒ Re ρ = ½",550,240,43,C.ink,1210,130);
            var left=650,right=1700,top=455,bottom=890,middle=(left+right)/2;
            rect(c,"Symbolic critical strip",left,top,right-left,bottom-top,[.045,.075,.12],C.edge,2,0);
            for(var y=top;y<bottom;y+=25)line(c,"Critical line segment "+y,middle,y,middle,Math.min(y+13,bottom),C.ink,2);
            text(c,"Sigma zero","σ = 0",left-30,910,30,C.muted);text(c,"Sigma half","σ = ½",middle-35,910,30,C.ink);text(c,"Sigma one","σ = 1",right-70,910,30,C.muted);
            arrow(c,"Unbounded height",middle,top+55,middle,top-35,C.ink,3);
            text(c,"Unbounded height label","unbounded height",middle+35,top-47,28,C.muted);
            rect(c,"Three starting points band",middle-110,660,220,140,null,C.cyan,2,12);
            for(var k=0;k<3;k++)ellipse(c,"Selected start "+k,middle,687+k*40,13,13,branchColors[k],null,0);
            text(c,"Finite sample label","three selected\rstarting zeros",middle+145,690,30,C.cyan,330,95);
            text(c,"Untested implication","Other zeros are not\rexcluded by these paths.",705,505,31,C.muted,340,125);
            text(c,"Open proof obligation","The global exclusion remains a separate proof obligation.",550,990,30,C.amber,1240,70);
        }
        function voiceFile(scene) {
            var value=CONFIG.voice?CONFIG.voice[scene.id]:null,path=value;
            if(value && typeof value==="object")path=value.path || value.file;
            var choices=[];
            if(path)choices.push(new File(path));
            choices.push(new File(CONFIG.output+"/assets/voice/"+scene.id+".mp3"));
            choices.push(new File(CONFIG.output+"/assets/voice/"+scene.id+".wav"));
            for(var k=0;k<choices.length;k++)if(choices[k].exists)return choices[k];
            throw Error("Missing narration clip for "+scene.id+"; expected assets/voice/"+scene.id+".mp3 or .wav");
        }
        var builders=[scopeScene,originScene,priorWorkScene,priorResultsScene,trackingScene,resultScene,methodsScene,confinementScene,globalScene];
        for(si=0;si<story.scenes.length;si++) {
            var scene=story.scenes[si],c=baseScene(scene,si);builders[si](c,scene);
            var vf=voiceFile(scene),audio=app.project.importFile(new ImportOptions(vf));
            if(!audio.hasAudio || audio.duration<=0 || audio.duration>scene.durationSeconds-.3)
                throw Error("Narration must fit without truncation: "+scene.id+" has "+audio.duration+" seconds for "+scene.durationSeconds+" second scene.");
            var al=c.layers.add(audio);al.name="VOICE • "+scene.id;al.startTime=.15;al.inPoint=.15;al.outPoint=.15+audio.duration;
            voiceRecords.push(scene.id+": "+audio.duration.toFixed(3)+"s / "+scene.durationSeconds+"s; "+vf.fsName);
            var layer=master.layers.add(c);layer.name=(si+1)+" • "+scene.title;layer.startTime=scene.startSeconds;
            layer.inPoint=scene.startSeconds;layer.outPoint=scene.startSeconds+scene.durationSeconds;
            var opacity=transform(layer,"ADBE Opacity");opacity.setValueAtTime(layer.inPoint,0);opacity.setValueAtTime(layer.inPoint+.25,100);
            opacity.setValueAtTime(layer.outPoint-.25,100);opacity.setValueAtTime(layer.outPoint,0);
        }
        master.openInViewer();master.time=story.scenes[5].startSeconds+story.scenes[5].durationSeconds-2;
        var rq=app.project.renderQueue.items.add(master);rq.applyTemplate("Best Settings");
        rq.outputModule(1).applyTemplate("H.264 - Match Render Settings - 15 Mbps");
        rq.outputModule(1).file=new File(CONFIG.output+"/presentation.mp4");
        app.project.save(saved);
        report("SAVED — RENDER QUEUED, NOT STARTED\n"+app.version+"\nDuration: "+master.duration+"\nFrame size: 1920x1080 @ 24\n"+
               "Master scenes: "+master.numLayers+"\nNarration words: "+story.narrationWordCount+"\n"+voiceRecords.join("\n"));
        app.endSuppressDialogs(false);
    } catch(e) {
        report("ERROR line "+e.line+": "+e.toString());
        app.endSuppressDialogs(false);
    }
})();
