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
