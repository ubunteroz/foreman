# python imports
from os import path
import sys, traceback
# library imports
from werkzeug import ClosingIterator, Request, SharedDataMiddleware, DebuggedApplication, Response
from werkzeug.exceptions import HTTPException, NotFound, InternalServerError, Forbidden
from werkzeug.routing import Map, Rule
from werkzeug.contrib.sessions import FilesystemSessionStore
# local imports
from controllers import controller_lookup
from controllers.baseController import BaseController
from utils.utils import ROOT_DIR, local_manager, local, session, config

sys.path.append('foreman')

staticLocations = {
    '/css': path.join(ROOT_DIR, 'static', 'css'),
    '/images': path.join(ROOT_DIR, 'static', 'images'),
    '/javascript': path.join(ROOT_DIR, 'static', 'javascript'),
    '/evidence_photos': path.join(ROOT_DIR, 'static', 'evidence_photos'),
    '/evidence_qr_code': path.join(ROOT_DIR, 'static', 'evidence_QR_codes'),
    '/evidence_custody_receipts': path.join(ROOT_DIR, 'static', 'evidence_custody_receipts'),
}


def make_app():
    application = Application()
    application = SharedDataMiddleware(application, staticLocations)    
    application = local_manager.make_middleware(application)

    if config.getboolean('debugging', 'debug') is True:
        application = DebuggedApplication(application, evalex=True)
    return application


class Application(object):    
    def __init__(self):
        self.session_store = FilesystemSessionStore()
        self.url_map = self.make_url_map()

    def __call__(self, environ, start_response):
        local.application = self
        request = Request(environ)
        self.load_session(request)
        response = None
        try:    
            adapter = self.url_map.bind_to_environ(environ)
            endpoint, vars = adapter.match()
            if 'userid' not in request.session and endpoint != "general.register":
                endpoint = 'general.login'
            response = self.dispatch(request, adapter, endpoint, vars)
        except NotFound:
            b = BaseController(request, adapter)
            response = b.return_404()
        except InternalServerError:
            request.environ['wsgi.errors'].write(traceback.format_exc())
            b = BaseController(request, adapter)
            response = b.return_500()
        except Forbidden:
            b = BaseController(request, adapter)
            response = b.return_403()
        except HTTPException, e:
            request.environ['wsgi.errors'].write(traceback.format_exc())
            response = e
        finally:
            session.close()
            if response:
                self.save_session(request, response)
        return ClosingIterator(response(environ, start_response),[local_manager.cleanup])

    def load_session(self, request):
        sid = request.cookies.get('foreman')
        if sid is None:
            request.session = self.session_store.new()
        else:
            request.session = self.session_store.get(sid)

    def save_session(self, request, response): 
        if request.session.should_save:
            self.session_store.save(request.session)
            response.set_cookie('foreman', request.session.sid)

    def dispatch(self, request, adapter, endpoint, vars):
        ctrl_str, act_str = endpoint.split('.')
        
        controller = controller_lookup[ctrl_str](request, adapter)
        method_to_call = getattr(controller, act_str)

        try:
            response = method_to_call(**vars)
        except:
            session.rollback()
            raise
        else:            
            session.commit()
            return response

    @staticmethod
    def make_url_map():
        map = Map()
        # general pages
        map.add(Rule('/', endpoint='general.index'))

        map.add(Rule('/login/', endpoint='general.login'))
        map.add(Rule('/logout/', endpoint='general.logout'))
        map.add(Rule('/register/', endpoint='general.register'))

        map.add(Rule('/admin/', endpoint='general.admin'))

        map.add(Rule('/cases/', endpoint='case.view_all'))
        map.add(Rule('/cases/<case_id>/', endpoint='case.view'))
        map.add(Rule('/cases/add/', endpoint='case.add'))
        map.add(Rule('/cases/edit/<case_id>/', endpoint='case.edit'))
        map.add(Rule('/cases/close/<case_id>/', endpoint='case.close'))
        map.add(Rule('/cases/change_status/<case_id>/', endpoint='case.change_status'))

        map.add(Rule('/tasks/', endpoint='task.view_all'))
        map.add(Rule('/tasks/qa/', endpoint='task.view_qas'))
        map.add(Rule('/cases/<case_id>/<task_id>/assign_me/', endpoint='task.assign_work'))
        map.add(Rule('/cases/<case_id>/<task_id>/assign/', endpoint='task.assign_work_manager'))
        map.add(Rule('/cases/<case_id>/<task_id>/', endpoint='task.view'))
        map.add(Rule('/cases/<case_id>/tasks/add/', endpoint='task.add'))
        map.add(Rule('/cases/<case_id>/<task_id>/edit/', endpoint='task.edit'))
        map.add(Rule('/cases/<case_id>/<task_id>/close/', endpoint='task.close'))
        map.add(Rule('/cases/<case_id>/<task_id>/change_status/', endpoint='task.change_status'))
        map.add(Rule('/cases/<case_id>/change_statuses/', endpoint='task.change_statuses'))

        map.add(Rule('/evidence/', endpoint='evidence.view_all'))
        map.add(Rule('/evidence/<evidence_id>/associate/', endpoint='evidence.associate'))
        map.add(Rule('/cases/<case_id>/evidence/<evidence_id>/', endpoint='evidence.view'))
        map.add(Rule('/evidence/<evidence_id>/', endpoint='evidence.view_caseless'))
        map.add(Rule('/evidence/<evidence_id>/remove/', endpoint='evidence.remove'))
        map.add(Rule('/cases/<case_id>/evidence/add/', endpoint='evidence.add'))
        map.add(Rule('/cases/<case_id>/evidence/<evidence_id>/edit/', endpoint='evidence.edit'))
        map.add(Rule('/cases/<case_id>/evidence/<evidence_id>/remove/', endpoint='evidence.disassociate'))
        map.add(Rule('/cases/<case_id>/evidence/<evidence_id>/custody/check-out/', endpoint='evidence.custody_out'))
        map.add(Rule('/cases/<case_id>/evidence/<evidence_id>/custody/check-in/', endpoint='evidence.custody_in'))

        map.add(Rule('/cases/<case_id>/<task_id>/notes', endpoint='forensics.work'))
        map.add(Rule('/cases/<case_id>/<task_id>/qa', endpoint='forensics.qa'))

        map.add(Rule('/users/', endpoint='user.view_all'))
        map.add(Rule('/users/<user_id>/', endpoint='user.view'))
        map.add(Rule('/users/add/', endpoint='user.add'))
        map.add(Rule('/users/edit/<user_id>/', endpoint='user.edit'))
        map.add(Rule('/users/edit_password/<user_id>/', endpoint='user.edit_password'))

        # Static rules -- these never match, they're only used for building.
        for k in staticLocations:
            map.add(Rule('%s/<file>' % k, endpoint=k.strip('/'), build_only=True))

        return map
