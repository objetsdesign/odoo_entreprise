/* Visual customizer (style Zakeke), sans dependance externe.
   - Calques texte / image positionnes sur le produit (SVG).
   - Deplacement (drag), taille, rotation, couleur, police.
   - Apercu PNG genere a la soumission. */
(function () {
    "use strict";

    var uid = 0;

    function initCustomizer(root) {
        if (root.dataset.vcInit) {
            return;
        }
        root.dataset.vcInit = "1";

        var stage = root.querySelector(".o_vc_stage");
        var base = root.querySelector(".o_vc_base");
        var svg = base ? base.querySelector("svg") : null;
        var layersBox = root.querySelector(".o_vc_layers");
        var form = root.querySelector(".js_vc_form");
        var inspector = root.querySelector(".o_vc_inspector");
        if (!form || !stage || !layersBox) {
            return;
        }

        var layers = [];
        var selected = null;

        // Zone de personnalisation indicative
        var area = (root.getAttribute("data-area") || "").split(",").map(function (n) {
            return parseFloat(n);
        });

        function vb() {
            var w = 400, h = 440;
            if (svg) {
                var v = svg.getAttribute("viewBox");
                if (v) {
                    var p = v.split(/[ ,]+/);
                    w = parseFloat(p[2]) || w;
                    h = parseFloat(p[3]) || h;
                }
            }
            return { w: w, h: h };
        }

        function applyProductColor(color) {
            if (!svg) {
                return;
            }
            var target = root.getAttribute("data-color-target") || "#part_body";
            var el = null;
            try {
                el = svg.querySelector(target);
            } catch (e) {
                el = null;
            }
            if (!el) {
                el = svg.querySelector('[id="' + target.replace(/^#/, "") + '"]');
            }
            if (el) {
                el.setAttribute("fill", color);
                el.querySelectorAll("path,rect,circle,polygon,ellipse,g").forEach(
                    function (c) { c.setAttribute("fill", color); });
            }
        }

        root.querySelectorAll(".o_vc_color").forEach(function (sw) {
            sw.addEventListener("click", function () {
                applyProductColor(sw.getAttribute("data-color"));
                root.querySelectorAll(".o_vc_color").forEach(function (s) {
                    s.classList.remove("o_vc_color_selected");
                });
                sw.classList.add("o_vc_color_selected");
                form.querySelector("[name='color_id']").value = sw.getAttribute("data-id") || "";
                form.querySelector("[name='color_name']").value = sw.getAttribute("data-name") || "";
            });
        });

        function render(layer) {
            var el = layer.el;
            el.style.left = layer.x + "px";
            el.style.top = layer.y + "px";
            el.style.transform = "rotate(" + layer.rot + "deg)";
            if (layer.type === "text") {
                el.textContent = layer.text || " ";
                el.style.fontFamily = layer.font;
                el.style.color = layer.color;
                el.style.fontSize = layer.size + "px";
            } else {
                el.style.width = layer.size * 4 + "px";
            }
        }

        function select(layer) {
            selected = layer;
            layers.forEach(function (l) { l.el.classList.remove("o_vc_selected"); });
            if (!layer) {
                inspector.style.display = "none";
                return;
            }
            layer.el.classList.add("o_vc_selected");
            inspector.style.display = "block";
            var textOnly = inspector.querySelector(".js_vc_text_only");
            textOnly.style.display = layer.type === "text" ? "block" : "none";
            inspector.querySelector(".js_vc_text").value = layer.text || "";
            inspector.querySelector(".js_vc_font").value = layer.font || "Arial";
            inspector.querySelector(".js_vc_textcolor").value = layer.color || "#000000";
            inspector.querySelector(".js_vc_size").value = layer.size;
            inspector.querySelector(".js_vc_rotate").value = layer.rot;
        }

        function startDrag(layer, ev) {
            ev.preventDefault();
            select(layer);
            var rect = layersBox.getBoundingClientRect();
            var pt = ev.touches ? ev.touches[0] : ev;
            var offX = pt.clientX - rect.left - layer.x;
            var offY = pt.clientY - rect.top - layer.y;
            function move(e) {
                var p = e.touches ? e.touches[0] : e;
                layer.x = p.clientX - rect.left - offX;
                layer.y = p.clientY - rect.top - offY;
                render(layer);
            }
            function up() {
                document.removeEventListener("mousemove", move);
                document.removeEventListener("mouseup", up);
                document.removeEventListener("touchmove", move);
                document.removeEventListener("touchend", up);
            }
            document.addEventListener("mousemove", move);
            document.addEventListener("mouseup", up);
            document.addEventListener("touchmove", move, { passive: false });
            document.addEventListener("touchend", up);
        }

        function addTextLayer() {
            uid += 1;
            var el = document.createElement("div");
            el.className = "o_vc_layer o_vc_text";
            var layer = {
                id: uid, type: "text", el: el, text: "Votre texte",
                font: "Arial", color: "#000000", size: 28, rot: 0,
                x: layersBox.clientWidth / 2 - 50, y: layersBox.clientHeight / 2 - 15,
            };
            el.addEventListener("mousedown", function (e) { startDrag(layer, e); });
            el.addEventListener("touchstart", function (e) { startDrag(layer, e); }, { passive: false });
            layersBox.appendChild(el);
            layers.push(layer);
            render(layer);
            select(layer);
        }

        function addImageLayer(dataUrl) {
            uid += 1;
            var el = document.createElement("img");
            el.className = "o_vc_layer o_vc_img";
            el.src = dataUrl;
            var layer = {
                id: uid, type: "image", el: el, src: dataUrl,
                size: 30, rot: 0,
                x: layersBox.clientWidth / 2 - 60, y: layersBox.clientHeight / 2 - 60,
            };
            el.addEventListener("mousedown", function (e) { startDrag(layer, e); });
            el.addEventListener("touchstart", function (e) { startDrag(layer, e); }, { passive: false });
            layersBox.appendChild(el);
            layers.push(layer);
            render(layer);
            select(layer);
        }

        root.querySelector(".js_vc_add_text").addEventListener("click", addTextLayer);
        root.querySelector(".js_vc_add_image").addEventListener("change", function (e) {
            var file = e.target.files && e.target.files[0];
            if (!file) { return; }
            var reader = new FileReader();
            reader.onload = function () { addImageLayer(reader.result); };
            reader.readAsDataURL(file);
            e.target.value = "";
        });

        inspector.querySelector(".js_vc_text").addEventListener("input", function (e) {
            if (selected && selected.type === "text") { selected.text = e.target.value; render(selected); }
        });
        inspector.querySelector(".js_vc_font").addEventListener("change", function (e) {
            if (selected) { selected.font = e.target.value; render(selected); }
        });
        inspector.querySelector(".js_vc_textcolor").addEventListener("input", function (e) {
            if (selected) { selected.color = e.target.value; render(selected); }
        });
        inspector.querySelector(".js_vc_size").addEventListener("input", function (e) {
            if (selected) { selected.size = parseInt(e.target.value, 10); render(selected); }
        });
        inspector.querySelector(".js_vc_rotate").addEventListener("input", function (e) {
            if (selected) { selected.rot = parseInt(e.target.value, 10); render(selected); }
        });
        inspector.querySelector(".js_vc_delete").addEventListener("click", function () {
            if (!selected) { return; }
            selected.el.remove();
            layers = layers.filter(function (l) { return l !== selected; });
            select(null);
        });

        // Cadre indicatif de la zone de personnalisation
        if (area.length === 4 && !isNaN(area[0]) && svg) {
            var dim = vb();
            var guide = document.createElement("div");
            guide.className = "o_vc_area_guide";
            guide.style.left = (area[0] / dim.w * 100) + "%";
            guide.style.top = (area[1] / dim.h * 100) + "%";
            guide.style.width = (area[2] / dim.w * 100) + "%";
            guide.style.height = (area[3] / dim.h * 100) + "%";
            layersBox.appendChild(guide);
        }

        function buildDesignData() {
            return layers.map(function (l) {
                var o = {
                    type: l.type, x: l.x, y: l.y, size: l.size, rot: l.rot,
                };
                if (l.type === "text") {
                    o.text = l.text; o.font = l.font; o.color = l.color;
                } else {
                    o.src = l.src; o.w = l.el.clientWidth; o.h = l.el.clientHeight;
                }
                return o;
            });
        }

        // Apercu PNG : SVG rasterise + calques dessines au-dessus
        function generatePreview(callback) {
            var dim = vb();
            var W = dim.w, H = dim.h;
            var sx = layersBox.clientWidth ? W / layersBox.clientWidth : 1;
            var sy = layersBox.clientHeight ? H / layersBox.clientHeight : 1;
            var canvas = document.createElement("canvas");
            canvas.width = W; canvas.height = H;
            var ctx = canvas.getContext("2d");
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, W, H);

            function drawLayers() {
                layers.forEach(function (l) {
                    ctx.save();
                    if (l.type === "text") {
                        var fx = l.x * sx;
                        var fy = l.y * sy;
                        ctx.font = (l.size * sy) + "px " + l.font;
                        ctx.fillStyle = l.color;
                        ctx.textBaseline = "top";
                        var tw = ctx.measureText(l.text || "").width;
                        ctx.translate(fx, fy);
                        ctx.rotate(l.rot * Math.PI / 180);
                        ctx.fillText(l.text || "", 0, 0);
                        void tw;
                    } else {
                        var iw = l.el.clientWidth * sx;
                        var ih = l.el.clientHeight * sy;
                        ctx.translate(l.x * sx, l.y * sy);
                        ctx.rotate(l.rot * Math.PI / 180);
                        try { ctx.drawImage(l.el, 0, 0, iw, ih); } catch (e) { /* noop */ }
                    }
                    ctx.restore();
                });
                try { callback(canvas.toDataURL("image/png")); } catch (e) { callback(""); }
            }

            if (!svg) { return drawLayers(); }
            try {
                var clone = svg.cloneNode(true);
                clone.setAttribute("width", W);
                clone.setAttribute("height", H);
                clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                var xml = new XMLSerializer().serializeToString(clone);
                var src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(xml)));
                var img = new Image();
                img.onload = function () { ctx.drawImage(img, 0, 0, W, H); drawLayers(); };
                img.onerror = function () { drawLayers(); };
                img.src = src;
            } catch (e) {
                drawLayers();
            }
        }

        form.addEventListener("submit", function (ev) {
            ev.preventDefault();
            form.querySelector("[name='design_data']").value = JSON.stringify(buildDesignData());
            generatePreview(function (dataUrl) {
                form.querySelector("[name='preview_image']").value = dataUrl || "";
                HTMLFormElement.prototype.submit.call(form);
            });
        });
    }

    function run() {
        document.querySelectorAll(".o_vc_customizer").forEach(initCustomizer);
    }
    if (document.readyState !== "loading") { run(); }
    else { document.addEventListener("DOMContentLoaded", run); }
    window.addEventListener("load", run);
})();
