PIPELINE_CSS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'
PIPELINE_JS_COMPRESSOR = 'pipeline.compressors.yui.YUICompressor'

PIPELINE_CSS = {
    'screen': {
        'source_filenames': ('css/screen.css',),
        'output_filename': 'screen.css',
        'extra_context': {'media': 'screen,projection'},
    },
    'landing': {
        'source_filenames': ('css/landing.css',),
        'output_filename': 'landing.css',
        'extra_context': {'media': 'screen,projection'},
    },
}

PIPELINE_JS = {
    'vendor': {
        'source_filenames': (
            'js/vendor/andlog.js',
            'js/vendor/jquery-1.8.2.js',
            'js/vendor/bootstrap.js',
            'js/vendor/moment.js',
            'js/vendor/detect_timezone.js',
            'js/vendor/jquery.highlight.js',
            'js/vendor/waypoints.js',
            'js/vendor/underscore.js',
            'js/vendor/backbone.js',
        ),
        'output_filename': 'vendor.js',
    },
    'app': {
        'source_filenames': (
            'js/app/common.js',
            'js/app/app.js',
        ),
        'output_filename': 'app.js',
    },
    'logs': {
        'source_filenames': ('js/app/logs/default.js',),
        'output_filename': 'logs.js',
    },
    'manage_channel': {
        'source_filenames': (
            'js/vendor/handlebars.js',
            'js/vendor/jquery-ui-1.9.1.custom.js',
            'js/app/manage/default.js',
            'js/app/manage/models.js',
        ),
        'output_filename': 'channel.js',
    },
}
