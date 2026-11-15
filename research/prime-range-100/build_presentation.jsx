/* defines: graph.primes.range100.presentation
   Separately saved addition to the accepted brush presentation. */
(function(){
 app.beginSuppressDialogs();var sf=new File(CONFIG.output+"/build-status.txt");
 function report(s){sf.open("w");sf.encoding="UTF-8";sf.write(s);sf.close();}
 function norm(f){return f.fsName.replace(/\\/g,"/").toLowerCase();}
 try {
  var target=new File(CONFIG.output+"/presentation-with-finite-proof.aep");
  if(app.project&&(app.project.numItems>0||app.project.file)){
   if(!app.project.file||app.project.dirty||(norm(app.project.file)!==norm(target)&&norm(app.project.file)!==norm(new File(CONFIG.baseProject))))throw Error("Unrelated or unsaved project preserved.");
   app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
  }
  if(!CONFIG.reviewAccepted)throw Error("Certificate and content review required.");
  app.open(new File(CONFIG.baseProject));var full=null,repo=null;
  for(var i=1;i<=app.project.numItems;i++){
   var it=app.project.item(i);
   if(it instanceof CompItem&&it.name==="Presentation with formal conclusion")full=it;
   if(it instanceof CompItem&&it.name.indexOf("Explore the public project")>=0)repo=it;
   if(it instanceof FootageItem&&it.file){
    var path=it.file.fsName.replace(/\\/g,"/"),prefix=CONFIG.baseOutput+"/assets/";
    if(path.toLowerCase().indexOf(prefix.toLowerCase())===0){
     var f=new File(CONFIG.output+"/assets/"+path.substr(prefix.length));if(!f.exists)throw Error("Missing asset "+f.fsName);
     if(it.mainSource.isStill===false && /brush0000\.png$/i.test(path)){it.replaceWithSequence(f,true);it.mainSource.conformFrameRate=24;if(Math.abs(it.duration-12)>.01)throw Error("Circle sequence duration changed");}else it.replace(f);
    }
   }
  }
  if(!full||!repo||full.duration!==264)throw Error("Expected accepted264second master.");
  for(var ri=app.project.renderQueue.numItems;ri>=1;ri--)app.project.renderQueue.item(ri).remove();
  full.duration=320;var split=false;
  for(var li=1;li<=full.numLayers;li++){
   var l=full.layer(li);
   if(l.inPoint===150&&l.outPoint===264){var tail=l.duplicate();tail.name="Repository card after proof examples";tail.startTime+=56;tail.inPoint=308;tail.outPoint=320;l.outPoint=252;split=true;break;}
  }
  if(!split)throw Error("Missing expected concluding section for repository split.");
  var C={bg:[.035,.052,.09],card:[.064,.09,.145],edge:[.16,.24,.33],ink:[.94,.96,1],muted:[.65,.75,.85],cyan:[.36,.91,.94],amber:[1,.77,.33],violet:[.72,.56,.9],white:[1,1,1],face:[.98,.96,.88]};
  var story={scenes:[0,1]};
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
        function text(c,name,value,x,y,size,color,w,h,font) {
            var l=w?c.layers.addBoxText([w,h||180]):c.layers.addText(value);l.name=name;
            var p=l.property("ADBE Text Properties").property("ADBE Text Document"),d=p.value;
            d.text=value;d.font=font||"SegoeUI";d.fontSize=size;d.fillColor=color||C.ink;d.applyStroke=false;
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

  function math(c,name,s,x,y,size,w,h){return text(c,name,s,x,y,size,C.ink,w||1200,h||70,"CambriaMath");}
  function queued(c,file){var rq=app.project.renderQueue.items.add(c);rq.applyTemplate("Best Settings");rq.outputModule(1).applyTemplate("H.264 - Match Render Settings - 15 Mbps");rq.outputModule(1).file=new File(CONFIG.output+"/"+file);}
  function sceneWrap(c,s,id,start,file){
   var voice=app.project.importFile(new ImportOptions(new File(CONFIG.output+"/assets/voice/"+id+".mp3")));
   if(!voice.hasAudio||voice.duration>s.duration-.3)throw Error("Narration does not fit "+id);
   var vl=c.layers.add(voice);vl.startTime=.15;vl.inPoint=.15;vl.outPoint=.15+voice.duration;
   var wrap=app.project.items.addComp(s.title+" - insert",1920,1080,1,s.duration,24);wrap.bgColor=C.bg;
   rect(wrap,"Opaque backing",0,0,1920,1080,C.bg,null,0,0);
   var body=wrap.layers.add(c),op=transform(body,"ADBE Opacity");op.setValueAtTime(0,0);op.setValueAtTime(.25,100);op.setValueAtTime(s.duration-.25,100);op.setValueAtTime(s.duration,0);
   var layer=full.layers.add(wrap);layer.startTime=start;layer.inPoint=start;layer.outPoint=start+s.duration;queued(wrap,file);return voice.duration;
  }
  var s=CONFIG.scenes[0];s.durationSeconds=s.duration;var c=baseScene(s,0);
  text(c,"Claim status","EXACT INTEGER CERTIFICATE  •  CLASSICAL TRIAL DIVISION",550,250,27,C.cyan,1250,60);
  math(c,"Domain","2 ≤ n ≤ 100; composite n = ab, 2 ≤ a ≤ b",550,315,35,1250,65);
  for(var n=0;n<=100;n++){
   var row=CONFIG.records[n],prime=row.classification==="prime",x=550+(n%11)*57,y=410+Math.floor(n/11)*43;
   var color=prime?[.31,.17,.47]:[.10,.13,.19];if(n<2)color=[.19,.19,.21];
   rect(c,"Integer "+n+" "+row.classification,x,y,51,37,color,prime?C.violet:C.edge,1,6);
   text(c,"Number "+n,String(n),x+7,y+4,24,C.ink,45,32);
  }
  rect(c,"Proof details backing",1210,410,580,430,[.045,.075,.12],C.edge,1,16);
  math(c,"Small-factor bound","a ≤ √n ≤ 10",1240,445,42,525,70);
  math(c,"Trial-prime basis","q ∈ {2, 3, 5, 7}",1240,515,39,525,65);
  text(c,"Square-boundary rule","Check q² ≤ n, including equality.",1240,585,27,C.muted,520,60);
  math(c,"Prime witness","97 mod (2,3,5,7)",1240,655,32,520,60);
  math(c,"Prime remainders","= (1,1,2,6)",1240,700,32,520,60);
  math(c,"Composite witness","91 = 7 × 13",1240,770,38,520,65);
  text(c,"Counts","25 primes  •  74 composites  •  0 and 1 are neither",550,870,31,C.ink,1230,60);
  text(c,"Color meaning","Violet displays proved labels. It is not a brush prediction.",550,935,27,C.violet,1230,60);
  var d1=sceneWrap(c,s,"finite_prime",252,"finite-prime-scene.mp4");
  s=CONFIG.scenes[1];s.durationSeconds=s.duration;c=baseScene(s,1);
  text(c,"Model status","EXACT MODEL f(z) = z  •  CURRENT FUNCTION PHASE",550,250,28,C.cyan,1250,60);
  var colors=[[27/255,115/255,94/255],[136/255,102/255,39/255],[101/255,60/255,133/255],[39/255,77/255,136/255]];
  var cx=850,cy=600,h=185,positions=[[cx,cy-h],[cx-h,cy-h],[cx-h,cy],[cx,cy]];
  for(var q=0;q<4;q++)rect(c,"Function phase sector "+q,positions[q][0],positions[q][1],h,h,colors[q],null,0,0);
  ellipse(c,"Positive contour",cx,cy,260,260,null,C.ink,3);
  ellipse(c,"Zero - phase undefined",cx,cy,19,19,C.bg,C.ink,2);
  text(c,"Zero label","0",cx+15,cy+11,27,C.ink);
  var point=ellipse(c,"Counterclockwise contour point",cx+130,cy,15,15,C.amber,C.bg,2),pp=transform(point,"ADBE Position");
  for(var k=0;k<=128;k++){var a=2*Math.PI*k/128;pp.setValueAtTime(2+16*k/128,[cx+130*Math.cos(a),cy-130*Math.sin(a)]);}
  text(c,"Contour direction","C: COUNTERCLOCKWISE",650,820,25,C.cyan,420,60);
  math(c,"Contour parameter","z(t) = exp(it)",1150,395,38,650,65);
  math(c,"Parameter interval","0 ≤ t ≤ 2π",1150,455,35,650,65);
  math(c,"Boundary certificate","|f(z(t))| = 1 > 0",1150,535,36,650,65);
  math(c,"Winding certificate","Δ arg f = 2π",1150,615,39,650,65);
  math(c,"Zero count","P = 0  ⇒  N = 1",1150,695,39,650,65);
  text(c,"Model conclusion","Exactly one simple zero: z = 0.",1150,775,28,C.muted,640,75);
  text(c,"Zeta next step","For ζ: certify every contour segment and account for poles.",550,895,28,C.ink,1250,60);
  text(c,"Global obligation","A global RH proof still requires all heights.",550,950,28,C.amber,1250,60);
  text(c,"Sources","Phase plots: Wegert (2010)  •  Argument principle: DLMF 1.10.9",550,1015,21,C.muted,1250,45);
  var d2=sceneWrap(c,s,"phase_proof",280,"phase-proof-scene.mp4");
  var checkpoint=repo.layer("Source checkpoint").property("ADBE Text Properties").property("ADBE Text Document"),cp=checkpoint.value;cp.text="Source checkpoint: "+CONFIG.sourceCheckpoint.slice(0,12);checkpoint.setValue(cp);
  var trace=repo.layer("Trace root").property("ADBE Text Properties").property("ADBE Text Document"),tr=trace.value;tr.text="Trace: graph.primes.range100";trace.setValue(tr);
  var repoInsert=app.project.items.addComp("Updated proof source card",1920,1080,1,12,24);repoInsert.bgColor=C.bg;rect(repoInsert,"Backing",0,0,1920,1080,C.bg,null,0,0);
  var rl=repoInsert.layers.add(repo),ro=transform(rl,"ADBE Opacity");ro.setValueAtTime(0,0);ro.setValueAtTime(.25,100);queued(repoInsert,"updated-repository-card.mp4");
  full.openInViewer();full.time=263;app.project.save(target);
  report("SAVED - THREE SCENES QUEUED\n"+app.version+"\nFull:320s at24fps,1920x1080\nPrime:252-280s\nPhase model:280-308s\nRepository:308-320s\nVoice durations:"+d1+", "+d2+"\nCheckpoint:"+CONFIG.sourceCheckpoint);
  app.endSuppressDialogs(false);
 }catch(e){report("ERROR line "+e.line+": "+e.toString());app.endSuppressDialogs(false);}
})();
