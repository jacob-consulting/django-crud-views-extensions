"""Verifies the django-pipeline integration story WITHOUT any runtime coupling:
a project builds its PIPELINE config from source_files() and sets EMIT: False."""

from django.template import Context, Template

from crud_views_widget_datetimepicker.assets import source_files


def _write_dummy_sources(static_dir, version):
    files = source_files(version, minified=False)
    for path in [*files["js"], *files["css"]]:
        f = static_dir / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"/* {path} */\n")
    return files


def test_pipeline_bundle_compiles_in_order(settings, tmp_path):
    from django.core.signals import setting_changed

    # pipeline.conf reads settings.PIPELINE at import time; the test project's
    # base settings never define it, so seed an empty dict before the first import.
    settings.PIPELINE = {}
    import pipeline.conf

    # This installed pipeline version's reload_settings signal receiver assumes
    # settings.PIPELINE is always a dict. pytest-django's fixture teardown eventually
    # restores PIPELINE to "unset" (value=None), which crashes that receiver and fails
    # this test at teardown. We re-read pipeline.conf.settings manually below instead
    # of relying on the signal, so disconnect it -- no other test in this suite
    # depends on pipeline's auto-reload-on-setting_changed behavior.
    setting_changed.disconnect(pipeline.conf.reload_settings)

    version = "9.9.9"
    static_src = tmp_path / "static_src"
    static_root = tmp_path / "static_root"
    files = _write_dummy_sources(static_src, version)

    settings.STATICFILES_DIRS = [str(static_src)]
    settings.STATIC_ROOT = str(static_root)
    settings.STATICFILES_FINDERS = [
        "django.contrib.staticfiles.finders.FileSystemFinder",
        "django.contrib.staticfiles.finders.AppDirectoriesFinder",
        "pipeline.finders.PipelineFinder",
    ]
    settings.PIPELINE = {
        "PIPELINE_ENABLED": True,
        "JAVASCRIPT": {"main": {"source_filenames": files["js"], "output_filename": "bundle/main.js"}},
        "STYLESHEETS": {"main": {"source_filenames": files["css"], "output_filename": "bundle/main.css"}},
        "JS_COMPRESSOR": None,
        "CSS_COMPRESSOR": None,
        "COMPILERS": [],
    }
    # pipeline caches its settings object; force re-read after override
    pipeline.conf.settings = pipeline.conf.PipelineSettings(settings.PIPELINE)

    from pipeline.packager import Packager

    packager = Packager()
    package = packager.package_for("js", "main")
    packager.pack_javascripts(package)

    bundle = (static_root / "bundle" / "main.js").read_text()
    # plugin before init.js — the order jQuery-plugin bootstrapping requires
    assert bundle.index("jquery.datetimepicker.full.js") < bundle.index("init.js")

    package_css = packager.package_for("css", "main")
    packager.pack_stylesheets(package_css)
    assert (static_root / "bundle" / "main.css").exists()


def test_emit_false_suppresses_cv_js_output(settings):
    from crud_views.lib import assets as registry

    # simulate a project that moved the picker into a pipeline bundle
    snapshot = dict(registry._REGISTRY)
    try:
        registry._REGISTRY.clear()
        registry.register_assets(
            key="datetimepicker",
            js=source_files("2.5.21", minified=False)["js"],
            css=source_files("2.5.21", minified=False)["css"],
            emit=False,
        )
        html = Template("{% load crud_views %}{% cv_js %}").render(Context({}))
        assert "datetimepicker" not in html
        assert "crud_views/js/viewset.js" in html  # core untouched
    finally:
        registry._REGISTRY.clear()
        registry._REGISTRY.update(snapshot)
