/* Configurateur visuel : applique les couleurs en direct sur le SVG du produit
   et genere un apercu PNG envoye avec la demande de devis. */
(function () {
    "use strict";

    function applyColor(svg, target, color) {
        if (!svg || !color) {
            return;
        }
        var el = null;
        if (target) {
            try {
                el = svg.querySelector(target);
            } catch (e) {
                el = null;
            }
            if (!el) {
                var bare = target.replace(/^#/, "");
                el = svg.querySelector('[id="' + bare + '"]');
            }
        }
        if (el) {
            el.setAttribute("fill", color);
            el.querySelectorAll("path,rect,circle,polygon,ellipse,line,g").forEach(
                function (c) {
                    c.setAttribute("fill", color);
                }
            );
        } else {
            // Cible introuvable -> on recolore tout le dessin (retour visuel garanti)
            svg.querySelectorAll("path,rect,circle,polygon,ellipse").forEach(
                function (c) {
                    c.setAttribute("fill", color);
                }
            );
        }
    }

    function initConfigurator(root) {
        if (root.dataset.pcInit) {
            return;
        }
        root.dataset.pcInit = "1";

        var svg = root.querySelector(".o_pc_canvas svg");
        var form = root.querySelector(".js_pc_form");
        if (!form) {
            return;
        }
        var selection = {};
        var activePart = null;

        function setActivePart(btn) {
            root.querySelectorAll(".o_pc_part").forEach(function (b) {
                b.classList.remove("active", "btn-secondary");
                b.classList.add("btn-outline-secondary");
            });
            btn.classList.add("active", "btn-secondary");
            btn.classList.remove("btn-outline-secondary");
            activePart = {
                name: btn.getAttribute("data-name"),
                target: btn.getAttribute("data-target"),
            };
        }

        var partButtons = root.querySelectorAll(".o_pc_part");
        partButtons.forEach(function (btn, index) {
            var def = btn.getAttribute("data-default");
            if (def) {
                applyColor(svg, btn.getAttribute("data-target"), def);
            }
            btn.addEventListener("click", function () {
                setActivePart(btn);
            });
            if (index === 0) {
                setActivePart(btn);
            }
        });
        if (partButtons.length === 0) {
            activePart = { name: "Produit", target: null };
        }

        root.querySelectorAll(".o_pc_color").forEach(function (sw) {
            sw.addEventListener("click", function () {
                if (!activePart) {
                    activePart = { name: "Produit", target: null };
                }
                var hex = sw.getAttribute("data-color");
                applyColor(svg, activePart.target, hex);
                selection[activePart.target || "_all"] = {
                    part_name: activePart.name,
                    color_id: sw.getAttribute("data-id"),
                    color_name: sw.getAttribute("data-name"),
                    hex: hex,
                };
                root.querySelectorAll(".o_pc_color").forEach(function (s) {
                    s.classList.remove("o_pc_color_selected");
                });
                sw.classList.add("o_pc_color_selected");
            });
        });

        function generatePreview(callback) {
            try {
                if (!svg) {
                    return callback("");
                }
                var clone = svg.cloneNode(true);
                var w = 400, h = 440;
                var vb = svg.getAttribute("viewBox");
                if (vb) {
                    var p = vb.split(/[ ,]+/);
                    w = parseFloat(p[2]) || w;
                    h = parseFloat(p[3]) || h;
                }
                clone.setAttribute("width", w);
                clone.setAttribute("height", h);
                clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                var xml = new XMLSerializer().serializeToString(clone);
                var src = "data:image/svg+xml;base64," +
                    btoa(unescape(encodeURIComponent(xml)));
                var img = new Image();
                img.onload = function () {
                    try {
                        var canvas = document.createElement("canvas");
                        canvas.width = w;
                        canvas.height = h;
                        var ctx = canvas.getContext("2d");
                        ctx.fillStyle = "#ffffff";
                        ctx.fillRect(0, 0, w, h);
                        ctx.drawImage(img, 0, 0, w, h);
                        callback(canvas.toDataURL("image/png"));
                    } catch (e) {
                        callback("");
                    }
                };
                img.onerror = function () {
                    callback("");
                };
                img.src = src;
            } catch (e) {
                callback("");
            }
        }

        form.addEventListener("submit", function (ev) {
            ev.preventDefault();
            generatePreview(function (dataUrl) {
                form.querySelector("[name='preview_image']").value = dataUrl || "";
                form.querySelector("[name='config_data']").value =
                    JSON.stringify(Object.values(selection));
                HTMLFormElement.prototype.submit.call(form);
            });
        });
    }

    function run() {
        document.querySelectorAll(".o_pc_configurator").forEach(initConfigurator);
    }

    // Odoo charge ses scripts apres DOMContentLoaded : on couvre tous les cas.
    if (document.readyState !== "loading") {
        run();
    } else {
        document.addEventListener("DOMContentLoaded", run);
    }
    window.addEventListener("load", run);
})();
