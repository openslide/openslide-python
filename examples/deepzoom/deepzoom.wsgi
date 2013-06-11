import os, sys
from deepzoom_server import app as application, load_slide
application.config.update({
    'DEEPZOOM_SLIDE': '<full_path_to_slide>',
})
load_slide()