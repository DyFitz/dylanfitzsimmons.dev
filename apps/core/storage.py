from whitenoise.storage import CompressedManifestStaticFilesStorage


class StaticStorage(CompressedManifestStaticFilesStorage):
    """WhiteNoise's compressed, hashed storage, with the hashes carried into JavaScript imports.

    Without this, `import ... from "./modules/motion.js"` would load the unhashed
    file, which browsers can keep serving from cache after a deploy.
    """

    support_js_module_import_aggregation = True
