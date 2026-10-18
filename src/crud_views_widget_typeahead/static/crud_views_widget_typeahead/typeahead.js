/*
 * crud_views_widget_typeahead — default frontend (vanilla JS, Bootstrap 5 markup).
 *
 * Contract (see docs/reference/typeahead/skins.md): the visible input shows the label of the pk in the hidden input, except
 * while typing. Arrow keys preview text only; Enter selects when the list is open and never submits then.
 * Option text is built from text nodes and <mark> elements, never parsed from HTML strings.
 *
 * Activates on DOMContentLoaded and on "cv:modal:loaded" (dispatched by crud_views after injecting modal
 * content). Call window.cvTypeahead.init(root) for other dynamically added content.
 */
(function () {
    "use strict";

    function fmt(template, n) {
        return (template || "").replace("{n}", String(n));
    }

    /* Append text to el, wrapping case-insensitive matches of any word in <mark>. */
    function highlight(el, text, words) {
        const lower = text.toLowerCase();
        const ranges = [];
        words.forEach(function (word) {
            const w = word.toLowerCase();
            let i = w ? lower.indexOf(w) : -1;
            while (i !== -1) {
                ranges.push([i, i + w.length]);
                i = lower.indexOf(w, i + w.length);
            }
        });
        ranges.sort(function (a, b) {
            return a[0] - b[0];
        });
        const merged = [];
        ranges.forEach(function (r) {
            const last = merged[merged.length - 1];
            if (last && r[0] <= last[1]) {
                last[1] = Math.max(last[1], r[1]);
            } else {
                merged.push([r[0], r[1]]);
            }
        });
        let pos = 0;
        merged.forEach(function (r) {
            if (r[0] > pos) el.appendChild(document.createTextNode(text.slice(pos, r[0])));
            const mark = document.createElement("mark");
            mark.textContent = text.slice(r[0], r[1]);
            el.appendChild(mark);
            pos = r[1];
        });
        if (pos < text.length) el.appendChild(document.createTextNode(text.slice(pos)));
    }

    class Typeahead {
        constructor(root) {
            this.root = root;
            this.input = root.querySelector('input[role="combobox"]');
            this.hidden = root.querySelector('input[type="hidden"]');
            this.list = root.querySelector('[role="listbox"]');
            this.status = root.querySelector("[data-cv-typeahead-status]");
            this.clearButton = root.querySelector("[data-cv-typeahead-clear]");
            this.url = root.dataset.url;
            this.minChars = parseInt(root.dataset.minChars, 10) || 0;
            this.debounce = parseInt(root.dataset.debounce, 10) || 0;
            this.submitOnClear = root.dataset.submitOnClear === "true";
            this.committed = this.input.value; // label of the stored pk
            this.options = []; // [{value, label, el}]
            this.active = -1;
            this.timer = null;
            this.controller = null;
            this.listen();
        }

        listen() {
            this.input.addEventListener("input", () => this.onInput());
            this.input.addEventListener("keydown", (e) => this.onKeydown(e));
            this.input.addEventListener("focusout", () => this.settle());
            // keep focus in the input while clicking an option, so focusout does not close the list first
            this.list.addEventListener("mousedown", (e) => e.preventDefault());
            if (this.clearButton) this.clearButton.addEventListener("click", () => this.clear(true));
            if (this.input.form) this.input.form.addEventListener("submit", () => this.settle(), true);
        }

        isOpen() {
            return !this.list.hidden;
        }

        onInput() {
            this.cancelPending();
            if (this.input.value.trim().length < this.minChars) {
                this.close();
                return;
            }
            this.timer = setTimeout(() => this.fetch(), this.debounce);
        }

        onKeydown(e) {
            const open = this.isOpen();
            switch (e.key) {
                case "ArrowDown":
                case "ArrowUp":
                    e.preventDefault();
                    if (open) {
                        this.move(e.key === "ArrowDown" ? 1 : -1);
                    } else if (e.key === "ArrowDown") {
                        this.cancelPending();
                        this.fetch();
                    }
                    break;
                case "Enter":
                    if (open) {
                        e.preventDefault(); // never submit while the list is open
                        if (this.active >= 0) this.select(this.active);
                    } else if (this.input.value.trim() !== "" && this.input.value !== this.committed) {
                        // typed text that is not a selection (search pending or not yet run): submitting now would
                        // silently restore and save the previous value, so search instead
                        e.preventDefault();
                        this.cancelPending();
                        this.fetch();
                    }
                    break;
                case "Escape":
                    if (open) {
                        e.preventDefault();
                        this.close();
                        this.input.value = this.committed;
                    }
                    break;
                case "Tab":
                    this.close();
                    break;
            }
        }

        /* Blur and submit: cancel pending work, then restore the invariant. Emptied text clears the pk. */
        settle() {
            this.cancelPending();
            this.close();
            if (this.input.value.trim() === "") {
                if (this.hidden.value !== "") this.clear(false);
            } else {
                this.input.value = this.committed;
            }
        }

        cancelPending() {
            clearTimeout(this.timer);
            this.timer = null;
            if (this.controller) {
                this.controller.abort();
                this.controller = null;
            }
        }

        fetch() {
            const q = this.input.value.trim();
            if (q.length < this.minChars) {
                this.close();
                return;
            }
            const controller = new AbortController();
            this.controller = controller;
            const url = this.url + (this.url.indexOf("?") === -1 ? "?" : "&") + "q=" + encodeURIComponent(q);
            fetch(url, {signal: controller.signal, credentials: "same-origin", headers: {Accept: "application/json"}})
                .then((response) => {
                    if (!response.ok) throw new Error("HTTP " + response.status);
                    return response.json();
                })
                .then((data) => {
                    if (this.controller !== controller) return; // superseded
                    this.controller = null;
                    if (document.activeElement !== this.input) return; // focus left meanwhile
                    this.render(data, q);
                })
                .catch((err) => {
                    if (err.name === "AbortError" || this.controller !== controller) return;
                    this.controller = null;
                    this.close();
                    this.announce(this.root.dataset.i18nError);
                    console.warn("cv-typeahead:", err);
                });
        }

        render(data, q) {
            const words = q.split(/\s+/).filter(Boolean);
            const results = data.results || [];
            const count = data.count || 0;
            this.list.replaceChildren();
            this.options = [];
            this.active = -1;
            this.input.removeAttribute("aria-activedescendant");
            results.forEach((item, i) => {
                const li = document.createElement("li");
                li.id = this.list.id + "_" + i;
                li.className = "dropdown-item";
                li.setAttribute("role", "option");
                li.setAttribute("aria-selected", "false");
                highlight(li, String(item.label), words);
                li.addEventListener("click", () => this.select(i));
                this.list.appendChild(li);
                this.options.push({value: String(item.value), label: String(item.label), el: li});
            });
            if (!results.length) {
                this.info(this.root.dataset.i18nNone);
            } else if (count > results.length) {
                this.info(fmt(this.root.dataset.i18nMore, count - results.length));
            }
            this.open();
            this.announce(fmt(this.root.dataset.i18nCount, count));
        }

        info(text) {
            const li = document.createElement("li");
            li.className = "dropdown-item-text cv-typeahead-info";
            li.setAttribute("role", "option");
            li.setAttribute("aria-disabled", "true");
            li.textContent = text;
            this.list.appendChild(li);
        }

        move(delta) {
            const n = this.options.length;
            if (!n) return;
            let next = this.active + delta;
            if (next < 0) next = n - 1;
            if (next >= n) next = 0;
            this.setActive(next);
            this.input.value = this.options[next].label; // preview only: the pk does not change
        }

        setActive(index) {
            this.options.forEach((opt, i) => {
                const on = i === index;
                opt.el.classList.toggle("active", on);
                opt.el.setAttribute("aria-selected", on ? "true" : "false");
            });
            this.active = index;
            const el = this.options[index].el;
            this.input.setAttribute("aria-activedescendant", el.id);
            el.scrollIntoView({block: "nearest"});
        }

        select(index) {
            const opt = this.options[index];
            this.hidden.value = opt.value;
            this.input.value = opt.label;
            this.committed = opt.label;
            this.close();
            this.changed();
        }

        clear(fromButton) {
            this.cancelPending();
            this.hidden.value = "";
            this.input.value = "";
            this.committed = "";
            this.close();
            this.changed();
            if (!fromButton) return;
            if (this.submitOnClear && this.input.form) {
                this.input.form.requestSubmit();
            } else {
                this.input.focus();
            }
        }

        changed() {
            if (this.clearButton) this.clearButton.hidden = this.hidden.value === "";
            this.hidden.dispatchEvent(new Event("change", {bubbles: true}));
        }

        open() {
            this.list.hidden = false;
            this.list.classList.add("show");
            this.input.setAttribute("aria-expanded", "true");
        }

        close() {
            this.list.hidden = true;
            this.list.classList.remove("show");
            this.input.setAttribute("aria-expanded", "false");
            this.input.removeAttribute("aria-activedescendant");
            this.active = -1;
        }

        announce(text) {
            if (this.status) this.status.textContent = text || "";
        }
    }

    function init(root) {
        (root || document).querySelectorAll("[data-cv-typeahead]").forEach(function (el) {
            if (el.dataset.cvTypeaheadReady) return;
            el.dataset.cvTypeaheadReady = "1";
            new Typeahead(el);
        });
    }

    window.cvTypeahead = {init: init};

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () {
            init(document);
        });
    } else {
        init(document);
    }
    // crud_views dispatches this (bubbling) on #cv-modal after injecting modal content
    document.addEventListener("cv:modal:loaded", function (e) {
        init(e.target);
    });
    // crud_views (>= 0.29.4) dispatches this (bubbling) on each formset row added after page load
    document.addEventListener("cv:formset:row-added", function (e) {
        init(e.target);
    });
})();
