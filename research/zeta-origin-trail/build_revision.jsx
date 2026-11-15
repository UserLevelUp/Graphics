/* defines: graph.riemann.origin_trail.production
   Derive a separately saved project from the accepted conclusion AEP.
   Preserve prior media; add one editable four-color brush scene. */
(function () {
    app.beginSuppressDialogs();
    var status=new File(CONFIG.output+"/build-status.txt");
    function report(s){status.open("w");status.encoding="UTF-8";status.write(s);status.close();}
    function norm(f){return f.fsName.replace(/\\/g,"/").toLowerCase();}
    try {
        var targetFile=new File(CONFIG.output+"/presentation-with-trail.aep");
        if(app.project && (app.project.numItems>0 || app.project.file)) {
            var accepted=app.project.file && (norm(app.project.file)===norm(targetFile) || norm(app.project.file)===norm(new File(CONFIG.baseProject)));
            if(!accepted || app.project.dirty)throw Error("An unrelated or unsaved project is open; preserved without changes.");
            app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
        }
        app.open(new File(CONFIG.baseProject));
        var full=null,repoCard=null;
        for(var n=1;n<=app.project.numItems;n++) {
            var it=app.project.item(n);
            if(it instanceof CompItem && it.name==="Presentation with formal conclusion")full=it;
            if(it instanceof CompItem && it.name.indexOf("Explore the public project")>=0)repoCard=it;
            if(it instanceof FootageItem && it.file) {
                var original=it.file.fsName.replace(/\\/g,"/"),needle=CONFIG.baseOutput+"/assets/";
                if(original.toLowerCase().indexOf(needle.toLowerCase())===0) {
                    var replacement=new File(CONFIG.output+"/assets/"+original.substr(needle.length));
                    if(!replacement.exists)throw Error("Missing copied asset: "+replacement.fsName);
                    it.replace(replacement);
                }
            }
        }
        if(!full || !repoCard || full.duration!==252)throw Error("Expected accepted 252-second master and source card.");
        for(var ri=app.project.renderQueue.numItems;ri>=1;ri--)app.project.renderQueue.item(ri).remove();
        var C={bg:[.035,.052,.09],card:[.064,.09,.145],edge:[.16,.24,.33],ink:[.94,.96,1],muted:[.65,.75,.85],cyan:[.36,.91,.94],amber:[1,.77,.33],violet:[.72,.56,.9],white:[1,1,1],face:[.98,.96,.88]};
        var story={scenes:[0,1,2,3,4,5,6,7,8]};
/* Reused editable presenter/vector helpers from accepted continuation presentation. */
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

        var phaseColors=[[27/255,115/255,94/255],[136/255,102/255,39/255],[101/255,60/255,133/255],[39/255,77/255,136/255]];
        function axes(c,name,x,y,w,h) {
            arrow(c,name+" real axis",x,y+h/2,x+w,y+h/2,C.muted,2);
            arrow(c,name+" imaginary axis",x+w/2,y+h,x+w/2,y,C.muted,2);
        }
        var scene={title:"Move the output origin",durationSeconds:14,bubbles:["Four colors, one brush","Earlier marks remain"]};
        var c=baseScene(scene,1);c.name="Four-color brush - editable scene";
        text(c,"Family formula","Fₐ(s) = ζ(s) − a        a: 0 → 1",545,235,43,C.ink);
        rect(c,"Input diagram",545,330,570,450,[.045,.075,.12],C.edge,1,18);
        rect(c,"Output diagram",1180,330,590,450,[.045,.075,.12],C.edge,1,18);
        text(c,"Input heading","INPUT PLANE: s",575,358,30,C.cyan);
        text(c,"Output heading","OUTPUT PLANE: ζ(s)",1210,358,30,C.amber);
        axes(c,"Fixed input",600,440,450,260);
        text(c,"Fixed input note","The s-axes stay fixed",607,730,30,C.muted);
        var target=c.layers.addNull();target.name="Moving output origin rig";
        transform(target,"ADBE Position").setValueAtTime(1,[1335,570]);
        transform(target,"ADBE Position").setValueAtTime(12,[1600,570]);
        // For this horizontal sweep, the accumulated opaque stamp has this exact envelope.
        // Size and center move together, keeping x=1240 fixed throughout the stroke.
        for(var trail=0;trail<2;trail++) {
            var ty=475+trail*95;
            var band=rect(c,trail===0?"Persistent yellow brush trail":"Persistent purple brush trail",1240,ty,95,95,phaseColors[trail+1],null,0,0);
            var shape=band.property("ADBE Root Vectors Group").property("ADBE Vector Shape - Rect").property("ADBE Vector Rect Size");
            shape.setValueAtTime(1,[95,95]);shape.setValueAtTime(12,[360,95]);
            transform(band,"ADBE Position").setValueAtTime(1,[1287.5,ty+47.5]);
            transform(band,"ADBE Position").setValueAtTime(12,[1420,ty+47.5]);
        }
        for(var q=0;q<2;q++) {
            var tile=rect(c,q===0?"Moving green brush quadrant":"Moving blue brush quadrant",0,0,95,95,phaseColors[q===0?0:3],null,0,0);
            local(tile,target,[47.5,q===0?-47.5:47.5]);
        }
        line(c,"Output real rail",1240,570,1710,570,C.muted,2);
        local(line(c,"Moving local horizontal",-115,0,115,0,C.ink,2),target,[0,0]);
        local(line(c,"Moving local vertical",0,-115,0,115,C.ink,2),target,[0,0]);
        local(ellipse(c,"Moving target a",0,0,17,17,C.amber,C.bg,2),target,[0,0]);
        text(c,"Output zero label","0",1325,700,32,C.ink);text(c,"Output one label","1",1590,700,32,C.ink);
        text(c,"Brush history note","A four-color brush leaves a trail as it moves.",580,825,32,C.ink,1160,60);
        text(c,"Overwrite note","Later marks overwrite earlier colors.",580,890,30,C.muted,1160,60);
        var vf=app.project.importFile(new ImportOptions(new File(CONFIG.output+"/assets/voice/origin_public.mp3")));
        var voice=c.layers.add(vf);voice.name="Accepted public narration";voice.startTime=.15;voice.inPoint=.15;voice.outPoint=.15+vf.duration;
        var insert=app.project.items.addComp("Origin trail insert",1920,1080,1,14,24);insert.bgColor=C.bg;
        rect(insert,"Opaque transition backing",0,0,1920,1080,C.bg,null,0,0);
        var inside=insert.layers.add(c);var opacity=transform(inside,"ADBE Opacity");
        opacity.setValueAtTime(0,0);opacity.setValueAtTime(.25,100);opacity.setValueAtTime(13.75,100);opacity.setValueAtTime(14,0);
        var overlay=full.layers.add(insert);overlay.name="REVISED ORIGIN - persistent brush trail";overlay.startTime=14;overlay.inPoint=14;overlay.outPoint=28;overlay.audioEnabled=false;
        // Insert twelve seconds after the origin scene; split the imported prefix and its audio.
        var beforeLayers=[];for(var li=1;li<=full.numLayers;li++)beforeLayers.push(full.layer(li));
        full.duration=264;
        for(var li=0;li<beforeLayers.length;li++) {
            var layer=beforeLayers[li];
            if(layer.inPoint===0 && layer.outPoint===138) {
                var tail=layer.duplicate();tail.name=layer.name+" - after circle";
                tail.startTime=12;tail.inPoint=40;tail.outPoint=150;layer.outPoint=28;
            } else if(layer.inPoint===138 && layer.outPoint===252) {
                layer.startTime+=12;layer.inPoint=150;layer.outPoint=264;
            }
        }
        var circleScene={title:"The same brush draws a circle",durationSeconds:12,bubbles:["Keep the brush upright","Change the travel direction","New marks go on top"]};
        var circle=baseScene(circleScene,1);circle.name="Circular brush - editable scene";
        var badge=circle.layer("Scene progress").property("ADBE Text Properties").property("ADBE Text Document"),bd=badge.value;bd.text="BRUSH DEMO";badge.setValue(bd);
        text(circle,"Brush mode","FIXED BRUSH ORIENTATION  •  CLOCKWISE PATH",550,250,28,C.cyan,1230,60);
        var pngOptions=new ImportOptions(new File(CONFIG.output+"/assets/circle/brush0000.png"));pngOptions.sequence=true;pngOptions.forceAlphabetical=true;
        var painted=app.project.importFile(pngOptions);painted.mainSource.conformFrameRate=24;
        if(Math.abs(painted.duration-12)>.01)throw Error("Expected288circle frames at24fps");
        var history=circle.layers.add(painted);history.name="Accumulated opaque brush history";
        var brush=circle.layers.addNull();brush.name="Fixed-orientation brush center";
        var position=transform(brush,"ADBE Position");
        for(var pi=0;pi<CONFIG.circlePositions.length;pi++) {
            var sample=CONFIG.circlePositions[pi];position.setValueAtTime(sample.time,[sample.x,sample.y]);
        }
        var frame=rect(circle,"Current brush outline",-48,-48,96,96,null,C.ink,2,0);local(frame,brush,[0,0]);
        local(ellipse(circle,"Current brush center",0,0,10,10,C.ink,C.bg,2),brush,[0,0]);
        text(circle,"History label","PAINT HISTORY",1090,585,24,C.muted,180,50);
        text(circle,"Circle note","Direction changes the trailing colors. New marks overwrite earlier colors.",550,920,29,C.ink,1230,65);
        var cv=app.project.importFile(new ImportOptions(new File(CONFIG.output+"/assets/voice/circle.mp3")));
        if(cv.duration>11.7)throw Error("Circle narration exceeds available scene duration");
        var cl=circle.layers.add(cv);cl.startTime=.15;cl.inPoint=.15;cl.outPoint=.15+cv.duration;
        var circleInsert=app.project.items.addComp("Circle brush insert",1920,1080,1,12,24);circleInsert.bgColor=C.bg;
        rect(circleInsert,"Opaque transition backing",0,0,1920,1080,C.bg,null,0,0);
        var circleBody=circleInsert.layers.add(circle),co=transform(circleBody,"ADBE Opacity");
        co.setValueAtTime(0,0);co.setValueAtTime(.25,100);co.setValueAtTime(11.75,100);co.setValueAtTime(12,0);
        var added=full.layers.add(circleInsert);added.name="NEW CIRCLE - fixed four-color brush";added.startTime=28;added.inPoint=28;added.outPoint=40;
        var source=repoCard.layer("Source checkpoint").property("ADBE Text Properties").property("ADBE Text Document");
        var doc=source.value;doc.text="Source checkpoint: "+CONFIG.sourceCheckpoint.slice(0,12);source.setValue(doc);
        var trace=repoCard.layer("Trace root").property("ADBE Text Properties").property("ADBE Text Document");
        var td=trace.value;td.text="Trace: graph.riemann.origin_trail";trace.setValue(td);
        var repoRender=app.project.items.addComp("Repository card insert",1920,1080,1,12,24);repoRender.bgColor=C.bg;
        rect(repoRender,"Opaque transition backing",0,0,1920,1080,C.bg,null,0,0);
        var repoBody=repoRender.layers.add(repoCard),repoOpacity=transform(repoBody,"ADBE Opacity");repoOpacity.setValueAtTime(0,0);repoOpacity.setValueAtTime(.25,100);
        var items=[insert,circleInsert,repoRender],names=["origin-trail-scene.mp4","circle-brush-scene.mp4","repository-card.mp4"];
        for(var k=0;k<items.length;k++) {
            var rq=app.project.renderQueue.items.add(items[k]);rq.applyTemplate("Best Settings");
            rq.outputModule(1).applyTemplate("H.264 - Match Render Settings - 15 Mbps");
            rq.outputModule(1).file=new File(CONFIG.output+"/"+names[k]);
        }
        full.openInViewer();full.time=26;
        app.project.save(targetFile);
        report("SAVED - THREE SCENES QUEUED\n"+app.version+"\nMaster: 264s, 1920x1080 @24\nOrigin interval:14-28s\nCircle interval:28-40s\nNative brush trail: x1240 to moving origin; y475-570 yellow, y570-665 purple\nCircle narration: "+cv.duration+"s\nCheckpoint: "+CONFIG.sourceCheckpoint);
        app.endSuppressDialogs(false);
    } catch(e) {report("ERROR line "+e.line+": "+e.toString());app.endSuppressDialogs(false);}
})();
