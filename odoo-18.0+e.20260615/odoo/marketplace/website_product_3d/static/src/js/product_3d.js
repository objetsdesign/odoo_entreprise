/* ============================================================
   Configurateur 3D v3
   - Matériaux séparés par partie (corps, anse, rebord, intérieur…)
   - Couleur unique OU par partie
   - Logo/image drag-and-drop repositionnable sous la vue 3D
   - Taille logo par slider
   ============================================================ */
(function () {
    "use strict";

    var THREE_URL = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js";
    var GLTF_URL  = "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js";
    var pending = null;
    function loadScript(src, cb) {
        var s = document.createElement("script");
        s.src = src;
        s.onload = function () { cb(true); };
        s.onerror = function () { cb(false); };
        document.head.appendChild(s);
    }
    function loadThree(cb) {
        if (window.THREE && window.THREE.GLTFLoader) { return cb(); }
        if (pending) { pending.push(cb); return; }
        pending = [cb];
        function done() { var q = pending; pending = null; q.forEach(function(f){ f(); }); }
        function afterCore() {
            if (window.THREE && window.THREE.GLTFLoader) { return done(); }
            loadScript(GLTF_URL, function () { done(); });
        }
        if (window.THREE) { afterCore(); }
        else { loadScript(THREE_URL, function (ok) { if (ok) { afterCore(); } else { pending = null; } }); }
    }

    /* ────────────────────────────────────────────────────────────
       CONSTRUCTEURS DE PRODUITS
       Chaque produit retourne { group, parts }
       parts = { body, handle, rim, inner, … } → MeshStandardMaterial
    ──────────────────────────────────────────────────────────── */

    function makeMat(THREE, hex, rough, metal) {
        return new THREE.MeshStandardMaterial({ color: hex, roughness: rough||0.72, metalness: metal||0.02 });
    }

    /* ── TASSE ── */
    function buildMug(THREE) {
        var parts = {
            body:   makeMat(THREE, 0xf5f3ef, 0.72, 0.02),
            handle: makeMat(THREE, 0xf5f3ef, 0.72, 0.02),
            rim:    makeMat(THREE, 0xf5f3ef, 0.72, 0.02),
            inner:  makeMat(THREE, 0x5a3e2b, 0.70, 0.01)
        };
        var g = new THREE.Group();
        g.add(new THREE.Mesh(new THREE.CylinderGeometry(1.15, 0.98, 2.5, 64), parts.body));
        var rimM = new THREE.Mesh(new THREE.TorusGeometry(1.15, 0.06, 16, 64), parts.rim);
        rimM.position.y = 1.25; rimM.rotation.x = Math.PI/2; g.add(rimM);
        var innerM = new THREE.Mesh(new THREE.CylinderGeometry(1.07, 0.95, 0.2, 64), parts.inner);
        innerM.position.y = 1.16; g.add(innerM);
        var handleM = new THREE.Mesh(new THREE.TorusGeometry(0.72, 0.16, 20, 48, Math.PI*1.25), parts.handle);
        handleM.position.set(1.18, 0, 0); handleM.rotation.z = -Math.PI*0.62; g.add(handleM);
        return { group: g, parts: parts };
    }

    /* ── SAC À MAIN ── */
    function buildHandbag(THREE) {
        var parts = {
            body:   makeMat(THREE, 0xc8954a, 0.65, 0.02),
            flap:   makeMat(THREE, 0xb07830, 0.65, 0.02),
            seam:   makeMat(THREE, 0x1e0f05, 0.95, 0.01),
            metal:  makeMat(THREE, 0x8a7050, 0.30, 0.85),
            handle: makeMat(THREE, 0x1a0e06, 0.65, 0.02),
            base:   makeMat(THREE, 0xc8954a, 0.65, 0.02)
        };
        var g = new THREE.Group();
        var bodyGeo = new THREE.BoxGeometry(3.4, 2.2, 1.6, 4, 4, 4);
        var pos = bodyGeo.attributes.position;
        for (var i=0; i<pos.count; i++) {
            if (pos.getY(i)>0.5) { pos.setX(i,pos.getX(i)*0.88); pos.setZ(i,pos.getZ(i)*0.88); }
        }
        pos.needsUpdate=true; bodyGeo.computeVertexNormals();
        g.add(new THREE.Mesh(bodyGeo, parts.body));
        var flapM = new THREE.Mesh(new THREE.SphereGeometry(1.72,32,16,0,Math.PI*2,0,Math.PI*0.48), parts.flap);
        flapM.scale.set(1,0.38,0.47); flapM.position.set(0,1.1,0); g.add(flapM);
        var stitch = new THREE.Mesh(new THREE.TorusGeometry(1.72,0.035,8,80,Math.PI), parts.seam);
        stitch.scale.set(1,0.38,0.47); stitch.position.set(0,1.1,0.75); stitch.rotation.x=Math.PI*0.5; g.add(stitch);
        var clasp = new THREE.Mesh(new THREE.BoxGeometry(0.28,0.18,0.12), parts.metal);
        clasp.position.set(0,1.12,0.82); g.add(clasp);
        var ring = new THREE.Mesh(new THREE.TorusGeometry(0.1,0.025,8,20), parts.metal);
        ring.position.set(0,1.22,0.82); ring.rotation.x=Math.PI*0.5; g.add(ring);
        [[-0.85,Math.PI*0.08],[0.85,-Math.PI*0.08]].forEach(function(p){
            var h = new THREE.Mesh(new THREE.TorusGeometry(0.62,0.09,16,48,Math.PI), parts.handle);
            h.position.set(p[0],2.05,0); h.rotation.x=Math.PI*0.5; h.rotation.z=p[1]; g.add(h);
        });
        var attGeo = new THREE.CylinderGeometry(0.07,0.07,0.32,12);
        [[-1.38],[-0.32],[0.32],[1.38]].forEach(function(p){
            var a=new THREE.Mesh(attGeo,parts.metal); a.position.set(p[0],1.15,0); g.add(a);
        });
        g.add(new THREE.Mesh(new THREE.BoxGeometry(0.04,2.1,1.62), parts.seam));
        var base = new THREE.Mesh(new THREE.CylinderGeometry(1.72,1.72,0.12,40), parts.base);
        base.scale.set(1,1,0.48); base.position.set(0,-1.16,0); g.add(base);
        g.position.y=-0.3;
        return { group: g, parts: parts };
    }

    /* ── VASE ── */
    function buildVase(THREE) {
        var parts = {
            body: makeMat(THREE, 0xd8d0c4, 0.88, 0.02),
            lip:  makeMat(THREE, 0xc8bfb0, 0.80, 0.02),
            inner:makeMat(THREE, 0x3a3028, 0.90, 0.01)
        };
        var g = new THREE.Group();
        var pts = [
            new THREE.Vector2(0.0,-1.6), new THREE.Vector2(0.55,-1.6),
            new THREE.Vector2(0.88,-1.5), new THREE.Vector2(1.18,-1.2),
            new THREE.Vector2(1.42,-0.8), new THREE.Vector2(1.55,-0.3),
            new THREE.Vector2(1.55,0.2),  new THREE.Vector2(1.48,0.7),
            new THREE.Vector2(1.30,1.1),  new THREE.Vector2(1.05,1.4),
            new THREE.Vector2(0.75,1.6),  new THREE.Vector2(0.50,1.72),
            new THREE.Vector2(0.42,1.9),  new THREE.Vector2(0.40,2.1),
            new THREE.Vector2(0.44,2.2),  new THREE.Vector2(0.46,2.25)
        ];
        g.add(new THREE.Mesh(new THREE.LatheGeometry(pts,64), parts.body));
        var inner=new THREE.Mesh(new THREE.CircleGeometry(0.38,32), parts.inner);
        inner.position.y=2.22; inner.rotation.x=-Math.PI/2; g.add(inner);
        var lip=new THREE.Mesh(new THREE.TorusGeometry(0.43,0.05,8,40), parts.lip);
        lip.position.y=2.22; lip.rotation.x=Math.PI/2; g.add(lip);
        var bottom=new THREE.Mesh(new THREE.CircleGeometry(0.54,40), parts.body);
        bottom.position.y=-1.62; bottom.rotation.x=Math.PI/2; g.add(bottom);
        g.position.y=-0.4;
        return { group: g, parts: parts };
    }

    /* ── BOX / CYLINDER ── */
    function buildBox(THREE) {
        var parts = { body: makeMat(THREE,0xf5f3ef,0.72,0.02) };
        var g=new THREE.Group();
        g.add(new THREE.Mesh(new THREE.BoxGeometry(2.2,2.2,2.2), parts.body));
        return { group:g, parts:parts };
    }
    function buildCylinder(THREE) {
        var parts = { body: makeMat(THREE,0xf5f3ef,0.72,0.02) };
        var g=new THREE.Group();
        g.add(new THREE.Mesh(new THREE.CylinderGeometry(1.2,1.2,2.6,64), parts.body));
        return { group:g, parts:parts };
    }

    function buildProduct(THREE, shape) {
        if (shape==="handbag")  return buildHandbag(THREE);
        if (shape==="vase")     return buildVase(THREE);
        if (shape==="box")      return buildBox(THREE);
        if (shape==="cylinder") return buildCylinder(THREE);
        return buildMug(THREE);
    }

    /* Labels lisibles pour chaque partie */
    var PART_LABELS = {
        body:"Corps", handle:"Anse / poignée", rim:"Rebord",
        inner:"Intérieur", flap:"Rabat", seam:"Coutures",
        metal:"Métal / fermoir", base:"Base", lip:"Lèvre"
    };

    /* ────────────────────────────────────────────────────────────
       TEXTURE COMPOSITE : couleur de fond + logo positionné librement
       logoX, logoY : 0–1 (position relative sur la texture UV)
       logoScale    : 0.1–0.8
    ──────────────────────────────────────────────────────────── */
    function buildCompositeCanvas(baseColor, logoSrc, logoX, logoY, logoScale, cb) {
        var C=1024, c=document.createElement("canvas");
        c.width=C; c.height=C;
        var ctx=c.getContext("2d");
        ctx.fillStyle = baseColor||"#f5f3ef";
        ctx.fillRect(0,0,C,C);
        if (!logoSrc) { return cb(c); }
        var img=new Image();
        img.onload=function(){
            var ratio=img.width/img.height;
            var scale=Math.max(0.08,Math.min(0.85,logoScale||0.35));
            var lw=Math.round(C*scale), lh=Math.round(lw/ratio);
            /* logoX, logoY sont le centre du logo en coordonnées relatives [0,1] */
            var tx=Math.round(C*(logoX||0.5) - lw/2);
            var ty=Math.round(C*(logoY||0.5) - lh/2);
            tx=Math.max(0,Math.min(C-lw,tx));
            ty=Math.max(0,Math.min(C-lh,ty));
            ctx.drawImage(img,tx,ty,lw,lh);
            cb(c);
        };
        img.onerror=function(){ cb(c); };
        img.src=logoSrc;
    }

    /* ────────────────────────────────────────────────────────────
       INIT
    ──────────────────────────────────────────────────────────── */
    function initOne(root) {
        if (root.dataset.p3dInit) { return; }
        root.dataset.p3dInit="1";
        var mount=root.querySelector(".o_p3d_stage");
        var form =root.querySelector(".js_p3d_form");
        if (!mount||!form) { return; }

        /* ── État global ── */
        var state = {
            /* Mode couleur : "single" ou "parts" */
            colorMode: "single",
            singleColor: "#f5f3ef",
            partColors: {},       /* { body:"#hex", handle:"#hex", … } */

            logoSrc:   null,
            logoX:     0.5,       /* centre UV horizontal */
            logoY:     0.5,       /* centre UV vertical   */
            logoScale: 0.35,

            /* Pour soumission formulaire */
            colorId:"", colorName:""
        };

        var productParts = null;  /* ref aux matériaux THREE */
        var THREE_ref = null;
        var bodyMatForLogo = null; /* matériau sur lequel on applique le logo (corps principal) */

        loadThree(function(){
            var THREE=window.THREE;
            THREE_ref=THREE;
            var W=mount.clientWidth||500, H=420;
            var scene=new THREE.Scene();
            var camera=new THREE.PerspectiveCamera(38,W/H,0.1,100);
            var dist=8.5;
            var renderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});
            renderer.setSize(W,H);
            renderer.setPixelRatio(window.devicePixelRatio||1);
            mount.appendChild(renderer.domElement);

            scene.add(new THREE.AmbientLight(0xffffff,0.85));
            var d1=new THREE.DirectionalLight(0xffffff,0.9); d1.position.set(5,9,7); scene.add(d1);
            var d2=new THREE.DirectionalLight(0xffffff,0.3); d2.position.set(-6,2,-4); scene.add(d2);
            var d3=new THREE.DirectionalLight(0xfff8f0,0.4); d3.position.set(0,-4,6); scene.add(d3);

            var glbUrl=(root.getAttribute("data-glb-url")||"").trim();
            var shape=root.getAttribute("data-shape")||"mug";
            var obj=null;          /* objet 3D affiché (groupe procédural OU modèle .glb) */
            var isGlb=!!glbUrl;

            /* Recentre + met à l'échelle un modèle importé pour qu'il tienne dans la vue */
            function fitImported(model){
                var box=new THREE.Box3().setFromObject(model);
                var size=new THREE.Vector3(); box.getSize(size);
                var center=new THREE.Vector3(); box.getCenter(center);
                var maxDim=Math.max(size.x,size.y,size.z)||1;
                var scale=3.2/maxDim;
                model.scale.setScalar(scale);
                /* recentre à l'origine après mise à l'échelle */
                model.position.set(
                    -center.x*scale, -center.y*scale, -center.z*scale);
                model.position.y-=0.3;
            }

            function placeProcedural(){
                var built=buildProduct(THREE,shape);
                productParts=built.parts;
                obj=built.group;
                obj.rotation.y=0.5; obj.rotation.x=0.05;
                scene.add(obj);
                bodyMatForLogo = productParts.body || Object.values(productParts)[0];
                Object.keys(productParts).forEach(function(k){
                    state.partColors[k]="#"+productParts[k].color.getHexString();
                });
                state.singleColor="#"+bodyMatForLogo.color.getHexString();
                applyColors();
            }

            /* Réfs pour la personnalisation d'un modèle .glb */
            var glbMats=[];          /* tous les matériaux du modèle (pour la teinte) */
            var glbOriginalMap=null; /* texture d'origine du matériau principal */
            var glbOriginalImage=null;

            if (isGlb && THREE.GLTFLoader) {
                /* Modèle réel importé (.glb), texture d'origine conservée.
                   La couleur agit comme teinte ; le logo se compose par-dessus. */
                productParts={};
                var grp=new THREE.Group(); scene.add(grp); obj=grp;
                grp.rotation.y=0.5;
                var loader=new THREE.GLTFLoader();
                loader.load(glbUrl, function(gltf){
                    var model=gltf.scene||gltf.scenes[0];
                    fitImported(model);
                    grp.add(model);

                    /* Récupère les matériaux et choisit le principal (celui qui porte une texture) */
                    var mainMat=null;
                    model.traverse(function(node){
                        if(!node.isMesh||!node.material) return;
                        var mats=Array.isArray(node.material)?node.material:[node.material];
                        mats.forEach(function(m){
                            if(glbMats.indexOf(m)===-1) glbMats.push(m);
                            if(!mainMat && m.map) mainMat=m;
                        });
                    });
                    if(!mainMat) mainMat=glbMats[0]||null;

                    if(mainMat){
                        bodyMatForLogo=mainMat;
                        productParts={body:mainMat};
                        glbOriginalMap=mainMat.map||null;
                        glbOriginalImage=(glbOriginalMap&&glbOriginalMap.image)||null;
                    }
                    /* Teinte neutre par défaut : on garde l'aspect d'origine */
                    state.singleColor="#ffffff";
                    renderer.render(scene,camera);
                }, undefined, function(){
                    /* échec de chargement : repli sur une forme générée */
                    isGlb=false; scene.remove(grp); obj=null; placeProcedural();
                });
            } else {
                if (isGlb) { isGlb=false; }   /* GLTFLoader indisponible -> repli */
                placeProcedural();
            }

            /* Place caméra */
            function place(){ camera.position.set(0,1,dist); camera.lookAt(0,0,0); }
            place();

            /* Orbite souris */
            var dragging=false, px=0, py=0, el=renderer.domElement;
            el.style.cursor="grab"; el.style.touchAction="none";
            el.addEventListener("pointerdown",function(e){ dragging=true; px=e.clientX; py=e.clientY; el.style.cursor="grabbing"; });
            window.addEventListener("pointerup",  function(){ dragging=false; el.style.cursor="grab"; });
            window.addEventListener("pointermove",function(e){
                if(!dragging||!obj) return;
                obj.rotation.y+=(e.clientX-px)*0.01;
                obj.rotation.x+=(e.clientY-py)*0.01;
                obj.rotation.x=Math.max(-0.9,Math.min(0.9,obj.rotation.x));
                px=e.clientX; py=e.clientY;
            });
            el.addEventListener("wheel",function(e){
                e.preventDefault();
                dist=Math.max(4,Math.min(16,dist+(e.deltaY>0?0.6:-0.6)));
                place();
            },{passive:false});

            /* ── Personnalisation d'un modèle .glb ──
               Teinte = multiplication de la matière par la couleur (texture conservée).
               Logo   = composé par-dessus la texture d'origine. */
            function refreshGlbTexture() {
                var tint=state.singleColor||"#ffffff";
                /* Applique la teinte sur TOUS les matériaux du modèle */
                glbMats.forEach(function(m){ if(m&&m.color){ m.color.set(tint); m.needsUpdate=true; } });

                var mat=bodyMatForLogo;
                if(!mat){ return; }

                /* Pas de logo : on garde la texture d'origine telle quelle */
                if(!state.logoSrc){
                    mat.map=glbOriginalMap||null;
                    mat.needsUpdate=true;
                    return;
                }

                /* Logo présent : dessine la texture d'origine puis le logo dessus */
                var C=1024, c=document.createElement("canvas"); c.width=C; c.height=C;
                var ctx=c.getContext("2d");
                if(glbOriginalImage){
                    try { ctx.drawImage(glbOriginalImage,0,0,C,C); }
                    catch(e){ ctx.fillStyle="#ffffff"; ctx.fillRect(0,0,C,C); }
                } else { ctx.fillStyle="#ffffff"; ctx.fillRect(0,0,C,C); }

                function applyCanvas(){
                    var tex=new THREE.CanvasTexture(c);
                    tex.flipY=false;                      /* glTF : pas de flip vertical */
                    if(glbOriginalMap){
                        if(glbOriginalMap.encoding!==undefined) tex.encoding=glbOriginalMap.encoding;
                        if(glbOriginalMap.colorSpace!==undefined) tex.colorSpace=glbOriginalMap.colorSpace;
                        tex.wrapS=glbOriginalMap.wrapS; tex.wrapT=glbOriginalMap.wrapT;
                        tex.flipY=glbOriginalMap.flipY;   /* respecte le réglage d'origine */
                    }
                    tex.needsUpdate=true;
                    mat.map=tex;
                    mat.needsUpdate=true;
                }

                var img=new Image();
                img.onload=function(){
                    var ratio=img.width/img.height;
                    var scale=Math.max(0.08,Math.min(0.85,state.logoScale||0.35));
                    var lw=Math.round(C*scale), lh=Math.round(lw/ratio);
                    var tx=Math.round(C*(state.logoX||0.5)-lw/2);
                    var ty=Math.round(C*(state.logoY||0.5)-lh/2);
                    tx=Math.max(0,Math.min(C-lw,tx));
                    ty=Math.max(0,Math.min(C-lh,ty));
                    ctx.drawImage(img,tx,ty,lw,lh);
                    applyCanvas();
                };
                img.onerror=applyCanvas;
                img.src=state.logoSrc;
            }

            /* ── Applique couleurs sur les parties THREE ── */
            function applyColors() {
                if(isGlb){ refreshGlbTexture(); return; }
                Object.keys(productParts).forEach(function(k){
                    var mat=productParts[k];
                    if(state.colorMode==="single") {
                        /* Corps = texture composite ; autres = couleur unique */
                        if(mat===bodyMatForLogo) {
                            refreshLogoTexture();
                        } else {
                            mat.map=null;
                            mat.color.set(state.singleColor);
                            mat.needsUpdate=true;
                        }
                    } else {
                        /* Chaque partie a sa propre couleur */
                        var c=state.partColors[k]||state.singleColor;
                        if(mat===bodyMatForLogo) {
                            /* logo uniquement sur le corps, même en mode parties */
                            refreshLogoTextureFor(mat, c);
                        } else {
                            mat.map=null;
                            mat.color.set(c);
                            mat.needsUpdate=true;
                        }
                    }
                });
            }

            function refreshLogoTexture() {
                refreshLogoTextureFor(bodyMatForLogo, state.singleColor);
            }

            function refreshLogoTextureFor(mat, baseColor) {
                buildCompositeCanvas(baseColor, state.logoSrc, state.logoX, state.logoY, state.logoScale, function(canvas){
                    var tex=new THREE.CanvasTexture(canvas);
                    tex.needsUpdate=true;
                    mat.map=tex;
                    mat.color.set(0xffffff);
                    mat.needsUpdate=true;
                });
            }

            /* Premier rendu */
            applyColors();

            /* ── Boucle rendu ── */
            function loop(){
                requestAnimationFrame(loop);
                if(obj && !dragging){ obj.rotation.y+=0.004; }
                renderer.render(scene,camera);
            }
            loop();

            /* ══════════════════════════════════════════════════════
               INTERFACE DOM
            ══════════════════════════════════════════════════════ */

            /* ── Tab : couleur unique vs parties ── */
            root.querySelectorAll(".o_p3d_mode_tab").forEach(function(tab){
                tab.addEventListener("click",function(){
                    root.querySelectorAll(".o_p3d_mode_tab").forEach(function(t){ t.classList.remove("active"); });
                    tab.classList.add("active");
                    state.colorMode=tab.getAttribute("data-mode");
                    root.querySelectorAll(".o_p3d_color_panel").forEach(function(p){ p.style.display="none"; });
                    var target=root.querySelector(".o_p3d_color_panel[data-panel='"+state.colorMode+"']");
                    if(target){ target.style.display="block"; }
                    applyColors();
                });
            });

            /* ── Swatches couleur UNIQUE ── */
            root.querySelectorAll(".o_p3d_color[data-scope='single']").forEach(function(s){
                s.addEventListener("click",function(){
                    state.singleColor=s.getAttribute("data-color");
                    state.colorId    =s.getAttribute("data-id")  ||"";
                    state.colorName  =s.getAttribute("data-name")||"";
                    form.querySelector("[name='color_id']").value  =state.colorId;
                    form.querySelector("[name='color_name']").value=state.colorName;
                    root.querySelectorAll(".o_p3d_color[data-scope='single']").forEach(function(x){ x.classList.remove("o_p3d_color_selected"); });
                    s.classList.add("o_p3d_color_selected");
                    /* En mode unique, toutes les parties prennent la même couleur */
                    if(state.colorMode==="single"){
                        Object.keys(state.partColors).forEach(function(k){ state.partColors[k]=state.singleColor; });
                    }
                    applyColors();
                });
            });

            /* ── Swatches couleur PAR PARTIE ── */
            root.querySelectorAll(".o_p3d_part_section").forEach(function(section){
                var partKey=section.getAttribute("data-part");
                section.querySelectorAll(".o_p3d_color[data-scope='part']").forEach(function(s){
                    s.addEventListener("click",function(){
                        state.partColors[partKey]=s.getAttribute("data-color");
                        section.querySelectorAll(".o_p3d_color[data-scope='part']").forEach(function(x){ x.classList.remove("o_p3d_color_selected"); });
                        s.classList.add("o_p3d_color_selected");
                        savePartColorsToForm();
                        applyColors();
                    });
                });
                /* Sélecteur couleur libre par partie */
                var picker=section.querySelector(".o_p3d_part_picker");
                if(picker){
                    picker.addEventListener("input",function(){
                        state.partColors[partKey]=picker.value;
                        section.querySelectorAll(".o_p3d_color[data-scope='part']").forEach(function(x){ x.classList.remove("o_p3d_color_selected"); });
                        savePartColorsToForm();
                        applyColors();
                    });
                }
            });

            /* Sélecteur couleur libre (mode unique) */
            var freePicker=root.querySelector(".o_p3d_free_color_picker");
            if(freePicker){
                freePicker.addEventListener("input",function(){
                    state.singleColor=freePicker.value;
                    root.querySelectorAll(".o_p3d_color[data-scope='single']").forEach(function(x){ x.classList.remove("o_p3d_color_selected"); });
                    if(state.colorMode==="single"){
                        Object.keys(state.partColors).forEach(function(k){ state.partColors[k]=state.singleColor; });
                    }
                    applyColors();
                });
            }

            function savePartColorsToForm(){
                var hid=form.querySelector("[name='part_colors']");
                if(hid){ hid.value=JSON.stringify(state.partColors); }
            }

            /* ────────────────────────────────────────────────────
               LOGO — Upload + drag sous la vue 3D
            ──────────────────────────────────────────────────── */
            var fileInput =root.querySelector(".o_p3d_file_input");
            var previewImg=root.querySelector(".o_p3d_img_preview");
            var uploadBtn =root.querySelector(".o_p3d_upload_btn");
            var clearBtn  =root.querySelector(".o_p3d_clear_btn");
            var hiddenB64 =form.querySelector("[name='custom_image_b64']");
            var statusTxt =root.querySelector(".o_p3d_upload_status");
            var scaleRange=root.querySelector(".o_p3d_logo_scale");
            var scaleVal  =root.querySelector(".o_p3d_logo_scale_val");
            var hiddenPos =form.querySelector("[name='logo_position']");
            var hiddenScaleF=form.querySelector("[name='logo_scale']");
            var logoCtrl  =root.querySelector(".o_p3d_logo_controls");

            /* Zone de repositionnement du logo */
            var logoDrop  =root.querySelector(".o_p3d_logo_drop");
            var logoDot   =root.querySelector(".o_p3d_logo_dot");
            var logoDropDragging=false, ldpx=0, ldpy=0;

            function updateLogoDot() {
                if(!logoDot||!logoDrop) return;
                var W2=logoDrop.offsetWidth, H2=logoDrop.offsetHeight;
                logoDot.style.left=(state.logoX*W2-12)+"px";
                logoDot.style.top =(state.logoY*H2-12)+"px";
            }

            if(logoDrop && logoDot){
                /* Drag du point logo */
                logoDot.addEventListener("pointerdown",function(e){
                    logoDropDragging=true;
                    e.stopPropagation();
                    e.preventDefault();
                    logoDot.setPointerCapture(e.pointerId);
                });
                logoDot.addEventListener("pointermove",function(e){
                    if(!logoDropDragging) return;
                    var rect=logoDrop.getBoundingClientRect();
                    state.logoX=Math.max(0,Math.min(1,(e.clientX-rect.left)/rect.width));
                    state.logoY=Math.max(0,Math.min(1,(e.clientY-rect.top)/rect.height));
                    updateLogoDot();
                    if(hiddenPos){ hiddenPos.value=JSON.stringify({x:state.logoX,y:state.logoY}); }
                    applyColors();
                });
                logoDot.addEventListener("pointerup",function(){ logoDropDragging=false; });

                /* Click direct sur la zone pour placer */
                logoDrop.addEventListener("click",function(e){
                    if(logoDropDragging) return;
                    var rect=logoDrop.getBoundingClientRect();
                    state.logoX=Math.max(0,Math.min(1,(e.clientX-rect.left)/rect.width));
                    state.logoY=Math.max(0,Math.min(1,(e.clientY-rect.top)/rect.height));
                    updateLogoDot();
                    if(hiddenPos){ hiddenPos.value=JSON.stringify({x:state.logoX,y:state.logoY}); }
                    applyColors();
                });
            }

            /* Taille logo */
            if(scaleRange){
                scaleRange.addEventListener("input",function(){
                    state.logoScale=parseFloat(scaleRange.value);
                    if(scaleVal){ scaleVal.textContent=Math.round(state.logoScale*100)+"%"; }
                    if(hiddenScaleF){ hiddenScaleF.value=state.logoScale; }
                    applyColors();
                });
            }

            /* Upload */
            if(uploadBtn&&fileInput){ uploadBtn.addEventListener("click",function(){ fileInput.click(); }); }
            if(fileInput){
                fileInput.addEventListener("change",function(){
                    var file=fileInput.files[0];
                    if(!file) return;
                    if(file.size>5*1024*1024){ statusTxt&&(statusTxt.textContent="⚠ Max 5 Mo"); return; }
                    statusTxt&&(statusTxt.textContent="Chargement…");
                    var reader=new FileReader();
                    reader.onload=function(ev){
                        var src=ev.target.result;
                        state.logoSrc=src;
                        if(previewImg){ previewImg.src=src; previewImg.style.display="block"; }
                        if(clearBtn){ clearBtn.style.display="inline-flex"; }
                        if(hiddenB64){ hiddenB64.value=src; }
                        if(logoCtrl){ logoCtrl.style.display="block"; }
                        /* Mettre l'aperçu dans la zone de drop */
                        var dropBg=root.querySelector(".o_p3d_logo_drop");
                        if(dropBg){ dropBg.style.backgroundImage="url('"+src+"')"; }
                        updateLogoDot();
                        applyColors();
                        statusTxt&&(statusTxt.textContent="✓ Logo appliqué");
                    };
                    reader.readAsDataURL(file);
                });
            }
            if(clearBtn){
                clearBtn.addEventListener("click",function(){
                    state.logoSrc=null;
                    if(previewImg){ previewImg.src=""; previewImg.style.display="none"; }
                    if(hiddenB64){ hiddenB64.value=""; }
                    if(fileInput){ fileInput.value=""; }
                    clearBtn.style.display="none";
                    statusTxt&&(statusTxt.textContent="");
                    if(logoCtrl){ logoCtrl.style.display="none"; }
                    var dropBg=root.querySelector(".o_p3d_logo_drop");
                    if(dropBg){ dropBg.style.backgroundImage="none"; }
                    applyColors();
                });
            }

            /* Submit */
            form.addEventListener("submit",function(ev){
                ev.preventDefault();
                try{
                    renderer.render(scene,camera);
                    form.querySelector("[name='preview_image']").value=renderer.domElement.toDataURL("image/png");
                }catch(e){}
                HTMLFormElement.prototype.submit.call(form);
            });
        }); /* fin loadThree */
    }

    function run(){ document.querySelectorAll(".o_p3d").forEach(initOne); }
    if(document.readyState!=="loading"){ run(); }
    else{ document.addEventListener("DOMContentLoaded",run); }
    window.addEventListener("load",run);
})();
