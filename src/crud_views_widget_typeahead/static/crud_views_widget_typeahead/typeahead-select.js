/*
 * crud_views_widget_typeahead — select popup frontend (vanilla JS, Bootstrap 5 markup).
 *
 * A trigger button shows the label of the pk in the hidden input. Opening it shows a popup with a search field and
 * a server-paged list; scrolling to the end loads the next page. Enter never submits while the popup is open; Escape
 * closes only the popup (a surrounding Bootstrap modal stays open). Option text is built from text nodes and <mark>
 * elements, never parsed from HTML strings; no inline styles are written.
 *
 * Activates on DOMContentLoaded and on "cv:modal:loaded" (dispatched by crud_views after injecting modal content).
 * Call window.cvTypeaheadSelect.init(root) for other dynamically added content.
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

    class TypeaheadSelect {
        constructor(root) {
            this.root = root;
            this.trigger = root.querySelector('button[aria-haspopup="listbox"]');
            this.labelEl = root.querySelector("[data-cv-typeahead-select-label]");
            this.clearButton = root.querySelector("[data-cv-typeahead-select-clear]");
            this.hidden = root.querySelector('input[type="hidden"]');
            this.popup = root.querySelector("[data-cv-typeahead-select-popup]");
            this.search = this.popup.querySelector('input[type="search"]');
            this.list = this.popup.querySelector('[role="listbox"]');
            this.status = root.querySelector("[data-cv-typeahead-select-status]");
            this.url = root.dataset.url;
            this.minChars = parseInt(root.dataset.minChars, 10) || 0;
            this.debounce = parseInt(root.dataset.debounce, 10) || 0;
            this.submitOnClear = root.dataset.submitOnClear === "true";
            this.options = []; // [{value, label, el}]
            this.active = -1;
            this.timer = null;
            this.controller = null;
            this.loadingEl = null;
            this.query = "";
            this.page = 0; // last page rendered for this.query; 0 = none
            this.count = 0;
            this.listen();
        }

        listen() {
            this.trigger.addEventListener("click", () => (this.isOpen() ? this.close(true) : this.open("")));
            this.trigger.addEventListener("keydown", (e) => this.onTriggerKeydown(e));
            // while open, a click on the trigger must not move focus out of the popup first (focusout would close,
            // then the click would reopen)
            this.trigger.addEventListener("mousedown", (e) => {
                if (this.isOpen()) e.preventDefault();
            });
            this.search.addEventListener("input", () => this.onInput());
            this.search.addEventListener("keydown", (e) => this.onSearchKeydown(e));
            // keep focus in the search field while clicking options or popup padding
            this.popup.addEventListener("mousedown", (e) => {
                if (e.target !== this.search) e.preventDefault();
            });
            this.popup.addEventListener("focusout", (e) => {
                if (!this.popup.contains(e.relatedTarget)) this.close(false);
            });
            this.list.addEventListener("scroll", () => this.maybeLoadMore());
            if (this.clearButton) this.clearButton.addEventListener("click", () => this.clear());
        }

        isOpen() {
            return !this.popup.hidden;
        }

        onTriggerKeydown(e) {
            // Enter and Space activate the button natively (click -> open); the button is type="button"
            if (e.key === "ArrowDown" || e.key === "ArrowUp") {
                e.preventDefault();
                if (!this.isOpen()) this.open("");
            } else if (e.key.length === 1 && e.key !== " " && !e.ctrlKey && !e.altKey && !e.metaKey) {
                e.preventDefault();
                if (!this.isOpen()) this.open(e.key);
            }
        }

        onSearchKeydown(e) {
            switch (e.key) {
                case "ArrowDown":
                case "ArrowUp":
                    e.preventDefault();
                    this.move(e.key === "ArrowDown" ? 1 : -1);
                    break;
                case "Enter":
                    e.preventDefault(); // never submit while the popup is open
                    if (this.active >= 0) this.select(this.active);
                    break;
                case "Escape":
                    e.preventDefault();
                    e.stopPropagation(); // a surrounding Bootstrap modal must stay open
                    this.close(true);
                    break;
                // Tab: focus leaves the popup, the focusout handler closes it
            }
        }

        open(seed) {
            this.popup.hidden = false;
            this.popup.classList.add("show");
            this.setExpanded(true);
            this.search.value = seed;
            this.search.focus();
            this.load();
        }

        close(focusTrigger) {
            if (!this.isOpen()) return;
            this.cancelPending();
            this.popup.hidden = true;
            this.popup.classList.remove("show");
            this.setExpanded(false);
            this.search.value = "";
            this.resetList();
            this.query = "";
            this.page = 0;
            this.count = 0;
            this.announce("");
            if (focusTrigger) this.trigger.focus();
        }

        setExpanded(on) {
            const value = on ? "true" : "false";
            this.trigger.setAttribute("aria-expanded", value);
            this.search.setAttribute("aria-expanded", value);
        }

        onInput() {
            clearTimeout(this.timer);
            this.timer = setTimeout(() => this.load(), this.debounce);
        }

        /* Start over for the search field's current text: page 1, or the "type more" hint. */
        load() {
            this.cancelPending();
            const q = this.search.value.trim();
            this.query = q;
            this.page = 0;
            this.count = 0;
            if (q.length < this.minChars) {
                this.resetList();
                this.info(this.root.dataset.i18nTypeMore);
                this.announce(this.root.dataset.i18nTypeMore);
                return;
            }
            this.fetchPage(1);
        }

        cancelPending() {
            clearTimeout(this.timer);
            this.timer = null;
            if (this.controller) {
                this.controller.abort();
                this.controller = null;
            }
            this.removeLoading();
        }

        fetchPage(page) {
            const q = this.query;
            const controller = new AbortController();
            this.controller = controller;
            if (page > 1) this.loadingEl = this.info(this.root.dataset.i18nLoading);
            const sep = this.url.indexOf("?") === -1 ? "?" : "&";
            const url = this.url + sep + "q=" + encodeURIComponent(q) + "&page=" + page;
            fetch(url, {signal: controller.signal, credentials: "same-origin", headers: {Accept: "application/json"}})
                .then((response) => {
                    if (!response.ok) throw new Error("HTTP " + response.status);
                    return response.json();
                })
                .then((data) => {
                    if (this.controller !== controller || q !== this.query || !this.isOpen()) return; // stale
                    this.controller = null;
                    this.render(data, page);
                })
                .catch((err) => {
                    if (err.name === "AbortError" || this.controller !== controller) return;
                    this.controller = null;
                    this.removeLoading();
                    this.info(this.root.dataset.i18nError);
                    this.announce(this.root.dataset.i18nError);
                    console.warn("cv-typeahead-select:", err);
                });
        }

        render(data, page) {
            const results = data.results || [];
            this.removeLoading();
            if (page === 1) this.resetList();
            this.count = data.count || 0;
            this.page = page;
            const words = this.query.split(/\s+/).filter(Boolean);
            results.forEach((item) => {
                const index = this.options.length;
                const li = document.createElement("li");
                li.id = this.list.id + "_" + index;
                li.className = "dropdown-item";
                li.setAttribute("role", "option");
                li.setAttribute("aria-selected", "false");
                highlight(li, String(item.label), words);
                li.addEventListener("click", () => this.select(index));
                this.list.appendChild(li);
                this.options.push({value: String(item.value), label: String(item.label), el: li});
            });
            if (page === 1) {
                if (!this.options.length) this.info(this.root.dataset.i18nNone);
                this.announce(
                    this.options.length ? fmt(this.root.dataset.i18nCount, this.count) : this.root.dataset.i18nNone
                );
            }
            this.maybeLoadMore(); // a short first page leaves nothing to scroll: keep filling
        }

        /* Load the next page when the list is scrolled (or filled) to within one row of its end. */
        maybeLoadMore() {
            if (this.controller || this.page === 0 || this.options.length >= this.count) return;
            const list = this.list;
            const row = this.options.length ? this.options[this.options.length - 1].el.offsetHeight : 0;
            if (list.scrollHeight - list.scrollTop - list.clientHeight <= row) this.fetchPage(this.page + 1);
        }

        resetList() {
            this.list.replaceChildren();
            this.options = [];
            this.active = -1;
            this.loadingEl = null;
            this.search.removeAttribute("aria-activedescendant");
        }

        info(text) {
            const li = document.createElement("li");
            li.className = "dropdown-item-text cv-typeahead-select-info";
            li.setAttribute("role", "option");
            li.setAttribute("aria-disabled", "true");
            li.textContent = text || "";
            this.list.appendChild(li);
            return li;
        }

        removeLoading() {
            if (this.loadingEl) {
                this.loadingEl.remove();
                this.loadingEl = null;
            }
        }

        move(delta) {
            const n = this.options.length;
            if (!n) return;
            let next = this.active + delta;
            if (next < 0) next = n - 1;
            if (next >= n) next = 0;
            this.setActive(next);
        }

        setActive(index) {
            this.options.forEach((opt, i) => {
                const on = i === index;
                opt.el.classList.toggle("active", on);
                opt.el.setAttribute("aria-selected", on ? "true" : "false");
            });
            this.active = index;
            const el = this.options[index].el;
            this.search.setAttribute("aria-activedescendant", el.id);
            el.scrollIntoView({block: "nearest"});
        }

        select(index) {
            const opt = this.options[index];
            this.hidden.value = opt.value;
            this.setLabel(opt.label, false);
            this.close(true);
            this.changed();
        }

        clear() {
            this.close(false);
            this.hidden.value = "";
            this.setLabel(this.root.dataset.i18nPlaceholder, true);
            this.changed();
            if (this.submitOnClear && this.hidden.form) {
                this.hidden.form.requestSubmit();
            } else {
                this.trigger.focus();
            }
        }

        setLabel(text, isPlaceholder) {
            this.labelEl.textContent = text || "";
            this.labelEl.classList.toggle("cv-typeahead-select-placeholder", isPlaceholder);
        }

        changed() {
            if (this.clearButton) this.clearButton.hidden = this.hidden.value === "";
            this.hidden.dispatchEvent(new Event("change", {bubbles: true}));
        }

        announce(text) {
            if (this.status) this.status.textContent = text || "";
        }
    }

    function init(root) {
        (root || document).querySelectorAll("[data-cv-typeahead-select]").forEach(function (el) {
            if (el.dataset.cvTypeaheadSelectReady) return;
            el.dataset.cvTypeaheadSelectReady = "1";
            new TypeaheadSelect(el);
        });
    }

    window.cvTypeaheadSelect = {init: init};

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
})();
