/* defines: graph.riemann.continuation.animation.aftereffects
   CONFIG is supplied by prepare_media.py; coordinates come from native evidence. */
(function () {
    app.beginSuppressDialogs();
    var log = new File(CONFIG.output + "/build-status.txt");
    function report(s) { log.open("w"); log.write(s); log.close(); }
    try {
        if (app.project && app.project.numItems > 0) {
            var old = app.project.file ? app.project.file.fsName.replace(/\\/g,"/") : "";
            var ownPartial = false;
            if(!old && app.project.numItems <= 2) for(var owned=1;owned<=app.project.numItems;owned++) if(app.project.item(owned).name === "Scientific animation") ownPartial=true;
            if (!ownPartial && old.indexOf("/continuation-ae/probe.aep") < 0 && old.indexOf("/riemann-continuation/") < 0)
                throw Error("Refusing to replace an unrelated open project: " + old);
            if(ownPartial) app.project.save(new File(CONFIG.output+"/failed-build.aep"));
            app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
        }
        app.newProject();
        var comp = app.project.items.addComp("Scientific animation",1920,1080,1,32,24);
        comp.bgColor = [0.035,0.052,0.09];
        var ink=[0.94,0.96,1], muted=[0.67,0.75,0.85], dark=[0.045,0.065,0.11];
        var colors=[[1,.88,.40],[.44,.94,1],[1,.59,.86]];
        var px=150,py=235,pw=1130,ph=620,lead=2,travel=26;
        function pos(s) { return [px+(s.real-.05)/2.95*pw,py+(30-s.imaginary)/20*ph]; }
        function text(name,value,x,y,size,color) {
            var l=comp.layers.addText(value); l.name=name;
            var d=l.property("ADBE Text Properties").property("ADBE Text Document").value;
            d.font="SegoeUI"; d.fontSize=size; d.fillColor=color||ink; d.applyStroke=false;
            l.property("ADBE Text Properties").property("ADBE Text Document").setValue(d);
            l.property("ADBE Transform Group").property("ADBE Position").setValue([x,y]); return l;
        }
        function shape(name,verts,color,width,closed,fill) {
            var l=comp.layers.addShape(); l.name=name;
            l.property("ADBE Transform Group").property("ADBE Position").setValue([0,0]);
            var root=l.property("ADBE Root Vectors Group");
            var path=root.addProperty("ADBE Vector Shape - Group");
            var s=new Shape(); s.vertices=verts; s.closed=!!closed;
            var z=[]; for(var i=0;i<verts.length;i++)z.push([0,0]); s.inTangents=z;s.outTangents=z;
            path.property("ADBE Vector Shape").setValue(s);
            if(fill) {var f=root.addProperty("ADBE Vector Graphic - Fill");f.property("ADBE Vector Fill Color").setValue(fill);}
            if(width) {var st=root.addProperty("ADBE Vector Graphic - Stroke");st.property("ADBE Vector Stroke Color").setValue(color);st.property("ADBE Vector Stroke Width").setValue(width);}
            return l;
        }
        function line(name,x1,y1,x2,y2,c,w) {return shape(name,[[x1,y1],[x2,y2]],c,w,false,null);}
        function rect(name,x,y,w,h,c) {return shape(name,[[x,y],[x+w,y],[x+w,y+h],[x,y+h]],null,0,true,c);}
        function circle(name,r,c) {
            var l=comp.layers.addShape();l.name=name;
            var root=l.property("ADBE Root Vectors Group"), e=root.addProperty("ADBE Vector Shape - Ellipse");
            e.property("ADBE Vector Ellipse Size").setValue([2*r,2*r]);
            var f=root.addProperty("ADBE Vector Graphic - Fill");f.property("ADBE Vector Fill Color").setValue(c);
            var st=root.addProperty("ADBE Vector Graphic - Stroke");st.property("ADBE Vector Stroke Color").setValue(dark);st.property("ADBE Vector Stroke Width").setValue(3);
            return l;
        }
        var io=new ImportOptions(new File(CONFIG.phase+"/phase0000.png"));io.sequence=true;io.forceAlphabetical=false;
        var footage=app.project.importFile(io);footage.mainSource.conformFrameRate=24;
        if(footage.width!==256 || footage.height!==256 || Math.abs(footage.duration-121/24)>.001) throw Error("Wrong phase sequence dimensions/count");
        var bg=comp.layers.add(footage);bg.name="Phase of zeta(s)-a | sampled 256 square";
        bg.property("ADBE Transform Group").property("ADBE Position").setValue([px+pw/2,py+ph/2]);
        bg.property("ADBE Transform Group").property("ADBE Scale").setValue([pw/footage.width*100,ph/footage.height*100]);
        bg.timeRemapEnabled=true;bg.outPoint=32;
        bg.property("ADBE Time Remapping").expression="Math.floor(Math.min(1,Math.max(0,(time-2)/26))*120+0.00001)/24";
        text("Title","A moving origin. Three tracked roots.",80,94,54);
        text("Equation","ζ(s) = a     •     ds/da = 1 / ζ′(s), locally when ζ′(s) ≠ 0",82,151,32,muted);
        text("Trace","GRAPH  /  RIEMANN  /  CONTINUATION",82,192,20,[.40,.77,.81]);
        line("Top border",px,py,px+pw,py,muted,1);
        line("Left border",px,py,px,py+ph,muted,1);
        line("Right boundary",px+pw,py,px+pw,py+ph,ink,2);
        line("Bottom border",px,py+ph,px+pw,py+ph,muted,1);
        var cx=pos({real:.5,imaginary:10})[0];
        for(var y=py;y<py+ph;y+=18)line("Critical line dash",cx,y,cx,Math.min(y+9,py+ph),[.8,.82,.86],1.5);
        text("Critical line label","σ = ½",cx-30,py-16,25,ink);
        var ticks=[.05,.5,1,1.5,2,2.5,3];
        for(var q=0;q<ticks.length;q++){var x=pos({real:ticks[q],imaginary:10})[0];line("Sigma tick",x,py+ph,x,py+ph+7,muted,1);text("Sigma "+ticks[q],String(ticks[q]),x-15,py+ph+38,27,muted);}
        for(var t=10;t<=30;t+=5){var yy=pos({real:.05,imaginary:t})[1];text("Height "+t,String(t),px-53,yy+9,27,muted);}
        text("Height label","height t",82,py-13,25,muted);
        text("Real label","real part σ",px+pw-135,py+ph+82,28,muted);
        var label=text("Current target","a = 0.000",1380,255,48,ink);
        label.property("ADBE Text Properties").property("ADBE Text Document").expression="'a = '+Math.min(1,Math.max(0,(time-2)/26)).toFixed(3)";
        line("Slider rail",1385,292,1810,292,muted,3);
        var slider=circle("Target slider",9,[.44,.94,1]);slider.property("ADBE Transform Group").property("ADBE Position").setValueAtTime(2,[1385,292]);slider.property("ADBE Transform Group").property("ADBE Position").setValueAtTime(28,[1810,292]);
        for(var j=0;j<CONFIG.data.trajectories.length;j++) {
            var b=CONFIG.data.trajectories[j],p=b.points,verts=[],lens=[0],sum=0;
            for(var k=0;k<p.length;k++){verts.push(pos(p[k].s));if(k){var dx=verts[k][0]-verts[k-1][0],dy=verts[k][1]-verts[k-1][1];sum+=Math.sqrt(dx*dx+dy*dy);lens.push(sum);}}
            // Native dashed complete path is labeled as precomputed, never a prediction.
            var future=shape(b.id+" precomputed future",verts,muted,2,false,null);
            var st=future.property("ADBE Root Vectors Group").property("ADBE Vector Graphic - Stroke");
            st.property("ADBE Vector Stroke Dashes").addProperty("ADBE Vector Stroke Dash 1").setValue(7);
            future.property("ADBE Transform Group").property("ADBE Opacity").setValue(48);
            var path=shape(b.id+" traversed samples",verts,colors[j],4,false,null);
            var trim=path.property("ADBE Root Vectors Group").addProperty("ADBE Vector Filter - Trim");
            var end=trim.property("ADBE Vector Trim End");
            var dot=circle(b.id+" interpolated display marker",9,colors[j]), dp=dot.property("ADBE Transform Group").property("ADBE Position");
            for(k=0;k<p.length;k++) {var tm=lead+travel*p[k].a;end.setValueAtTime(tm,100*lens[k]/sum);dp.setValueAtTime(tm,verts[k]);}
            for(k=1;k<=dp.numKeys;k++){dp.setInterpolationTypeAtKey(k,KeyframeInterpolationType.LINEAR);dp.setSpatialAutoBezierAtKey(k,false);dp.setSpatialTangentsAtKey(k,[0,0,0],[0,0,0]);}
            var seed=circle(b.id+" original zero",5,ink);seed.property("ADBE Transform Group").property("ADBE Position").setValue(verts[0]);
            text(b.id+" seed label",b.id,verts[0][0]-44,verts[0][1]+8,28,colors[j]);
            var cy=365+j*170;
            rect(b.id+" card",1360,cy-40,480,150,[.07,.10,.16]);
            text(b.id+" heading",b.id+"  •  known zero #"+(j+1),1382,cy,30,colors[j]);
            var stat=text(b.id+" status","TRACKING",1382,cy+44,29,ink);
            var expr=b.status=="exited"?"time < "+(lead+travel*b.endpoint.a)+" ? 'Tracking inside window' : 'EXIT at a ≈ "+b.endpoint.a.toFixed(6)+"'":"time < 28 ? 'Tracking inside window' : 'REACHED ζ(s) = 1'";
            stat.property("ADBE Text Properties").property("ADBE Text Document").expression=expr;
            text(b.id+" endpoint note",b.status=="exited"?"Square retains its exit target.":"Endpoint σ ≈ "+b.endpoint.s.real.toFixed(6),1382,cy+82,24,muted);
            if(b.status=="exited") {
                var stop=lead+travel*b.endpoint.a,v=verts[verts.length-1];
                var square=shape(b.id+" retained exit marker",[[v[0]-9,v[1]-9],[v[0]+9,v[1]-9],[v[0]+9,v[1]+9],[v[0]-9,v[1]+9]],colors[j],3,true,dark);
                square.inPoint=stop;dot.outPoint=stop;
            }
        }
        var phases=[[27/255,115/255,94/255],[136/255,102/255,39/255],[101/255,60/255,133/255],[39/255,77/255,136/255]];
        for(var c=0;c<4;c++){rect("Phase swatch "+c,1380+c*110,900,92,16,phases[c]);text("Phase angle "+c,(c*90)+"°",1380+c*110,945,24,muted);}
        text("Phase legend","Phase of ζ(s) − a",1380,865,27,ink);
        text("Path legend","SOLID: traversed samples   •   DASHED: precomputed later samples",80,958,29,ink);
        text("Display limit","Markers interpolate samples. Phase frames are discrete. Exits mean leaving this window, not disappearing.",80,1002,25,muted);
        text("Scientific limit","Finite numerical evidence • three supplied seeds • no certified continuation and no RH proof",80,1042,25,muted);
        comp.openInViewer();comp.time=28;
        var rq=app.project.renderQueue.items.add(comp);rq.applyTemplate("Best Settings");
        rq.outputModule(1).applyTemplate("H.264 - Match Render Settings - 15 Mbps");
        rq.outputModule(1).file=new File(CONFIG.output+"/scientific-animation.mp4");
        app.project.save(new File(CONFIG.output+"/scientific-animation.aep"));
        report("SAVED\n"+app.version+"\nLayers: "+comp.numLayers+"\nDuration: "+comp.duration);
        app.endSuppressDialogs(false);
    } catch(e) {report("ERROR line "+e.line+": "+e.toString());app.endSuppressDialogs(false);}
})();
