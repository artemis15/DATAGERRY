# DATAGERRY - OpenSource Enterprise CMDB
# Copyright (C) 2019 NETHINKS GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import logging
from datetime import datetime

import pytz
from bson import json_util
from flask import abort, jsonify, request, current_app

from cmdb.data_storage.database_utils import object_hook, default
from cmdb.framework import CmdbObject
from cmdb.framework.cmdb_errors import ObjectDeleteError, ObjectInsertError, ObjectManagerGetError, \
    ObjectManagerUpdateError
from cmdb.framework.cmdb_log import LogAction, CmdbObjectLog
from cmdb.framework.cmdb_log_manager import LogManagerInsertError
from cmdb.framework.cmdb_render import CmdbRender, RenderList, RenderError
from cmdb.interface.route_utils import make_response, RootBlueprint, insert_request_user, login_required, right_required
from cmdb.user_management import User

with current_app.app_context():
    object_manager = current_app.object_manager
    log_manager = current_app.log_manager
    user_manager = current_app.user_manager

try:
    from cmdb.utils.error import CMDBError
except ImportError:
    CMDBError = Exception

LOGGER = logging.getLogger(__name__)
object_blueprint = RootBlueprint('object_blueprint', __name__, url_prefix='/object')
with current_app.app_context():
    from cmdb.interface.rest_api.framework_routes.object_link_routes import link_rest

    object_blueprint.register_nested_blueprint(link_rest)


# DEFAULT ROUTES

@object_blueprint.route('/', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_object_list(request_user: User):
    """
    get all objects in database
    Args:
        request_user: auto inserted user who made the request.
    Returns:
        list of rendered objects
    """
    try:
        object_list = object_manager.get_all_objects()
        if request.args.get('start') is not None:
            start = int(request.args.get('start'))
            length = int(request.args.get('length'))
            object_list = object_list[start:start + length]

    except ObjectManagerGetError as err:
        LOGGER.error(err.message)
        return abort(404)
    if len(object_list) < 1:
        return make_response(object_list, 204)

    rendered_list = RenderList(object_list, request_user).render_result_list()

    return make_response(rendered_list)


@object_blueprint.route('/native', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_native_object_list(request_user: User):
    try:
        object_list = object_manager.get_all_objects()
    except CMDBError:
        return abort(404)
    resp = make_response(object_list)
    return resp


@object_blueprint.route('/iterate/<int:type_id>/', methods=['POST'])
@object_blueprint.route('/iterate/<int:type_id>', methods=['POST'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def iterate_over_type_object_list(type_id: int, request_user: User):
    """Generates a table response"""
    table_config = json.dumps(request.json)

    try:
        table_config = json.loads(table_config, object_hook=json_util.object_hook)
    except TypeError:
        return abort(400)

    LOGGER.debug(table_config)

    start_at = int(table_config['start'])
    site_length = int(table_config['length'])
    order_column = int(table_config['order'][0]['column'])
    order_direction = table_config['order'][0]['dir']
    if order_direction == 'asc':
        order_direction = 1
    else:
        order_direction = -1

    LOGGER.debug(table_config['columns'][order_column])

    try:
        object_list = object_manager.get_objects_by(type_id=type_id, direction=order_direction)
        to_render_list = object_list[start_at:start_at + site_length]
    except ObjectManagerGetError:
        return abort(404)

    rendered_list = RenderList(to_render_list, request_user).render_result_list()

    table_response = {
        'data': rendered_list,
        'recordsTotal': len(object_list),
        'recordsFiltered': len(object_list)
    }
    return make_response(table_response)


@object_blueprint.route('/type/<int:public_id>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_objects_by_type(public_id, request_user: User):
    """Return all objects by type_id"""

    try:
        object_list = object_manager.get_objects_by(sort="type_id", type_id=public_id)
    except CMDBError:
        return abort(400)

    if request.args.get('start') is not None:
        start = int(request.args.get('start'))
        length = int(request.args.get('length'))
        object_list = object_list[start:start + length]

    if len(object_list) < 1:
        return make_response(object_list, 204)

    rendered_list = RenderList(object_list, request_user).render_result_list()
    resp = make_response(rendered_list)
    return resp


@object_blueprint.route('/filter/<string:value>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_objects_by_searchterm(value, request_user: User):
    """Return all objects by search term"""
    try:
        type = {}
        term = value
        try:
            term = int(value)
        except:
            if value in ['True', 'true']:
                term = True
            elif value in ['False', 'false']:
                term = False
            elif isinstance(value, str):
                term = {'$regex': value}

        if request.args.get('type') is not None:
            type = {'type_id': int(request.args.get('type'))}

        query: dict = {'$and': [
            {'fields': {'$elemMatch': {'value': term}}},
            type
        ]}
        object_list = object_manager.get_objects_by(sort="type_id", **query)

        if request.args.get('start') is not None:
            start = int(request.args.get('start'))
            length = int(request.args.get('length'))
            object_list = object_list[start:start + length]

    except CMDBError:
        return abort(400)

    if len(object_list) < 1:
        return make_response(object_list, 204)

    rendered_list = RenderList(object_list, request_user).render_result_list()
    resp = make_response(rendered_list)
    return resp


@object_blueprint.route('/type/<string:type_ids>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_objects_by_types(type_ids):
    """Return all objects by type_id
    TODO: Refactore to render results"""
    try:
        query = _build_query({'type_id': type_ids}, q_operator='$or')
        all_objects_list = object_manager.get_objects_by(sort="type_id", **query)

    except CMDBError:
        return abort(400)

    resp = make_response(all_objects_list)
    return resp


@object_blueprint.route('/many/<string:public_ids>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_objects_by_public_id(public_ids):
    """Return all objects by public_ids
    TODO: Refactore to render results"""

    try:
        query = _build_query({'public_id': public_ids}, q_operator='$or')
        all_objects_list = object_manager.get_objects_by(sort="public_id", **query)

    except CMDBError:
        return abort(400)

    resp = make_response(all_objects_list)
    return resp


@object_blueprint.route('/count/<int:type_id>', methods=['GET'])
@login_required
def count_object_by_type(type_id):
    try:
        count = object_manager.count_objects_by_type(type_id)
        resp = make_response(count)
    except CMDBError:
        return abort(400)
    return resp


@object_blueprint.route('/count/', methods=['GET'])
@login_required
def count_objects():
    try:
        count = object_manager.count_objects()
        resp = make_response(count)
    except CMDBError:
        return abort(400)
    return resp


@object_blueprint.route('/<int:public_id>/', methods=['GET'])
@object_blueprint.route('/<int:public_id>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_object(public_id, request_user: User):
    try:
        object_instance = object_manager.get_object(public_id)
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)

    try:
        type_instance = object_manager.get_type(object_instance.get_type_id())
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)

    try:
        render = CmdbRender(object_instance=object_instance, type_instance=type_instance, render_user=request_user)
        render_result = render.result()
    except RenderError as err:
        LOGGER.error(err)
        return abort(500)

    resp = make_response(render_result)
    return resp


@object_blueprint.route('<int:public_id>/native/', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_native_object(public_id: int, request_user: User):
    try:
        object_instance = object_manager.get_object(public_id)
    except CMDBError:
        return abort(404)
    resp = make_response(object_instance)
    return resp


@object_blueprint.route('/reference/<int:public_id>/', methods=['GET'])
@object_blueprint.route('/reference/<int:public_id>', methods=['GET'])
@insert_request_user
def get_objects_by_reference(public_id: int, request_user: User):
    try:
        reference_list: list = object_manager.get_object_references(public_id=public_id)
        rendered_reference_list = RenderList(reference_list, request_user).render_result_list()
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)
    if len(reference_list) < 1:
        return make_response(rendered_reference_list, 204)
    return make_response(rendered_reference_list)


@object_blueprint.route('/user/<int:public_id>/', methods=['GET'])
@object_blueprint.route('/user/<int:public_id>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_objects_by_user(public_id: int, request_user: User):
    try:
        object_list = object_manager.get_objects_by(sort="type_id", author_id=public_id)
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(400)

    if len(object_list) < 1:
        return make_response(object_list, 204)

    rendered_list = RenderList(object_list, request_user).render_result_list()
    return make_response(rendered_list)


@object_blueprint.route('/user/new/<int:timestamp>/', methods=['GET'])
@object_blueprint.route('/user/new/<int:timestamp>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_new_objects_since(timestamp: int, request_user: User):
    request_date = datetime.fromtimestamp(timestamp, pytz.utc)
    query = {
        'creation_time': {
            '$gt': request_date
        }
    }
    try:
        object_list = object_manager.get_objects_by(sort="creation_time", **query)
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(400)

    if len(object_list) < 1:
        return make_response(object_list, 204)

    rendered_list = RenderList(object_list, request_user).render_result_list()
    return make_response(rendered_list)


@object_blueprint.route('/user/changed/<int:timestamp>/', methods=['GET'])
@object_blueprint.route('/user/changed/<int:timestamp>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_changed_objects_since(timestamp: int, request_user: User):
    request_date = datetime.fromtimestamp(timestamp, pytz.utc)
    query = {
        'last_edit_time': {
            '$gt': request_date,
            '$ne': None
        }
    }
    try:
        object_list = object_manager.get_objects_by(sort="creation_time", **query)
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(400)

    if len(object_list) < 1:
        return make_response(object_list, 204)

    rendered_list = RenderList(object_list, request_user).render_result_list()
    return make_response(rendered_list)


# CRUD routes

@object_blueprint.route('/', methods=['POST'])
@login_required
@insert_request_user
@right_required('base.framework.object.add')
def insert_object(request_user: User):
    from bson import json_util
    from datetime import datetime
    add_data_dump = json.dumps(request.json)

    try:
        new_object_data = json.loads(add_data_dump, object_hook=json_util.object_hook)
        new_object_data['public_id'] = object_manager.get_new_id(CmdbObject.COLLECTION)
        new_object_data['active'] = True
        new_object_data['creation_time'] = datetime.utcnow()
        new_object_data['views'] = 0
        new_object_data['version'] = '1.0.0'  # default init version
    except TypeError as e:
        LOGGER.warning(e)
        abort(400)

    try:
        new_object_id = object_manager.insert_object(new_object_data)
    except ObjectInsertError as oie:
        LOGGER.error(oie)
        return abort(500)

    # get current object state
    try:
        current_type_instance = object_manager.get_type(new_object_data['type_id'])
        current_object = object_manager.get_object(new_object_id)
        current_object_render_result = CmdbRender(object_instance=current_object,
                                                  type_instance=current_type_instance,
                                                  render_user=request_user).result()
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)
    except RenderError as err:
        LOGGER.error(err)
        return abort(500)

    # Generate new insert log
    try:
        log_params = {
            'object_id': new_object_id,
            'user_id': request_user.get_public_id(),
            'user_name': request_user.get_name(),
            'comment': 'Object was created',
            'render_state': json.dumps(current_object_render_result, default=default).encode('UTF-8'),
            'version': current_object.version
        }
        log_ack = log_manager.insert_log(action=LogAction.CREATE, log_type=CmdbObjectLog.__name__, **log_params)
    except LogManagerInsertError as err:
        LOGGER.error(err)

    resp = make_response(new_object_id)
    return resp


@object_blueprint.route('/<int:public_id>/', methods=['PUT'])
@object_blueprint.route('/<int:public_id>', methods=['PUT'])
@login_required
@insert_request_user
@right_required('base.framework.object.edit')
def update_object(public_id: int, request_user: User):
    # get current object state
    try:
        current_object_instance = object_manager.get_object(public_id)
        current_type_instance = object_manager.get_type(current_object_instance.get_type_id())
        current_object_render_result = CmdbRender(object_instance=current_object_instance,
                                                  type_instance=current_type_instance,
                                                  render_user=request_user).result()
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)
    except RenderError as err:
        LOGGER.error(err)
        return abort(500)

    update_comment = ''
    # load put data
    try:
        # get data as str
        add_data_dump = json.dumps(request.json)

        # convert into python dict
        put_data = json.loads(add_data_dump, object_hook=object_hook)
        # check for comment
        try:
            update_comment = put_data['comment']
            del put_data['comment']
        except (KeyError, IndexError, ValueError):
            update_comment = ''
    except TypeError as e:
        LOGGER.warning(e)
        return abort(400)

    # update edit time
    put_data['last_edit_time'] = datetime.utcnow()

    try:
        update_object_instance = CmdbObject(**put_data)
    except ObjectManagerUpdateError as err:
        LOGGER.error(err)
        return abort(400)

    # calc version

    changes = current_object_instance / update_object_instance

    if len(changes['new']) == 1:
        update_object_instance.update_version(update_object_instance.VERSIONING_PATCH)
    elif len(changes['new']) == len(update_object_instance.fields):
        update_object_instance.update_version(update_object_instance.VERSIONING_MAJOR)
    elif len(changes['new']) > (len(update_object_instance.fields) / 2):
        update_object_instance.update_version(update_object_instance.VERSIONING_MINOR)
    else:
        update_object_instance.update_version(update_object_instance.VERSIONING_PATCH)

    # insert object
    try:
        update_ack = object_manager.update_object(update_object_instance, request_user)
    except CMDBError as e:
        LOGGER.warning(e)
        return abort(500)

    try:
        # generate log
        log_data = {
            'object_id': public_id,
            'version': current_object_render_result.object_information['version'],
            'user_id': request_user.get_public_id(),
            'user_name': request_user.get_name(),
            'comment': update_comment,
            'changes': changes,
            'render_state': json.dumps(current_object_render_result, default=default).encode('UTF-8')
        }
        log_manager.insert_log(action=LogAction.EDIT, log_type=CmdbObjectLog.__name__, **log_data)
    except (CMDBError, LogManagerInsertError) as err:
        LOGGER.error(err)

    return make_response(update_ack)


@object_blueprint.route('/<int:public_id>', methods=['DELETE'])
@login_required
@insert_request_user
@right_required('base.framework.object.delete')
def delete_object(public_id: int, request_user: User):
    try:
        current_object_instance = object_manager.get_object(public_id)
        current_type_instance = object_manager.get_type(current_object_instance.get_type_id())
        current_object_render_result = CmdbRender(object_instance=current_object_instance,
                                                  type_instance=current_type_instance,
                                                  render_user=request_user).result()
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)
    except RenderError as err:
        LOGGER.error(err)
        return abort(500)

    try:
        ack = object_manager.delete_object(public_id=public_id, request_user=request_user)
    except ObjectDeleteError:
        return abort(400)
    except CMDBError:
        return abort(500)

    try:
        # generate log
        log_data = {
            'object_id': public_id,
            'version': current_object_render_result.object_information['version'],
            'user_id': request_user.get_public_id(),
            'user_name': request_user.get_name(),
            'comment': 'Object was deleted',
            'render_state': json.dumps(current_object_render_result, default=default).encode('UTF-8')
        }
        log_manager.insert_log(action=LogAction.DELETE, log_type=CmdbObjectLog.__name__, **log_data)
    except (CMDBError, LogManagerInsertError) as err:
        LOGGER.error(err)

    resp = make_response(ack)
    return resp


@object_blueprint.route('/delete/<string:public_ids>', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.delete')
def delete_many_objects(public_ids, request_user: User):
    try:
        ids = []
        operator_in = {'$in': []}
        filter_public_ids = {'public_id': {}}
        for v in public_ids.split(","):
            try:
                ids.append(int(v))
            except (ValueError, TypeError):
                return abort(400)
        operator_in.update({'$in': ids})
        filter_public_ids.update({'public_id': operator_in})

        ack = []
        objects = object_manager.get_objects_by(**filter_public_ids)

        for current_object_instance in objects:
            try:
                current_type_instance = object_manager.get_type(current_object_instance.get_type_id())
                current_object_render_result = CmdbRender(object_instance=current_object_instance,
                                                          type_instance=current_type_instance,
                                                          render_user=request_user).result()
            except ObjectManagerGetError as err:
                LOGGER.error(err)
                return abort(404)
            except RenderError as err:
                LOGGER.error(err)
                return abort(500)

            try:
                ack.append(object_manager.delete_object(public_id=current_object_instance.get_public_id(),
                                                        request_user=request_user))
            except ObjectDeleteError:
                return abort(400)
            except CMDBError:
                return abort(500)

            try:
                # generate log
                log_data = {
                    'object_id': current_object_instance.get_public_id(),
                    'version': current_object_render_result.object_information['version'],
                    'user_id': request_user.get_public_id(),
                    'user_name': request_user.get_name(),
                    'comment': 'Object was deleted',
                    'render_state': json.dumps(current_object_render_result, default=default).encode('UTF-8')
                }
                log_manager.insert_log(action=LogAction.DELETE, log_type=CmdbObjectLog.__name__, **log_data)
            except (CMDBError, LogManagerInsertError) as err:
                LOGGER.error(err)

        resp = make_response({'successfully': ack})
        return resp

    except ObjectDeleteError as e:
        return jsonify(message='Delete Error', error=e.message)
    except CMDBError:
        return abort(500)


# Special routes
@object_blueprint.route('/<int:public_id>/state/', methods=['GET'])
@object_blueprint.route('/<int:public_id>/state', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.activation')
def get_object_state(public_id: int, request_user: User):
    try:
        founded_object = object_manager.get_object(public_id=public_id)
    except ObjectManagerGetError as err:
        LOGGER.debug(err)
        return abort(404)
    return make_response(founded_object.active)


@object_blueprint.route('/<int:public_id>/state/', methods=['PUT'])
@object_blueprint.route('/<int:public_id>/state', methods=['PUT'])
@login_required
@insert_request_user
@right_required('base.framework.object.activation')
def update_object_state(public_id: int, request_user: User):
    if isinstance(request.json, bool):
        state = request.json
    else:
        return abort(400)
    try:
        founded_object = object_manager.get_object(public_id=public_id)
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)
    if founded_object.active == state:
        return make_response(False, 204)
    try:
        founded_object.active = state
        update_ack = object_manager.update_object(founded_object, request_user)
    except ObjectManagerUpdateError as err:
        LOGGER.error(err)
        return abort(500)

        # get current object state
    try:
        current_type_instance = object_manager.get_type(founded_object.get_type_id())
        current_object_render_result = CmdbRender(object_instance=founded_object,
                                                  type_instance=current_type_instance,
                                                  render_user=request_user).result()
    except ObjectManagerGetError as err:
        LOGGER.error(err)
        return abort(404)
    except RenderError as err:
        LOGGER.error(err)
        return abort(500)
    try:
        # generate log
        change = {
            'old': not state,
            'new': state
        }
        log_data = {
            'object_id': public_id,
            'version': founded_object.version,
            'user_id': request_user.get_public_id(),
            'user_name': request_user.get_name(),
            'render_state': json.dumps(current_object_render_result, default=default).encode('UTF-8'),
            'comment': 'Active status has changed',
            'changes': change,
        }
        log_manager.insert_log(action=LogAction.ACTIVE_CHANGE, log_type=CmdbObjectLog.__name__, **log_data)
    except (CMDBError, LogManagerInsertError) as err:
        LOGGER.error(err)

    return make_response(update_ack)


# SPECIAL ROUTES
@object_blueprint.route('/newest', methods=['GET'])
@object_blueprint.route('/newest/', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_newest(request_user: User):
    """
    get object with newest creation time
    Args:
        request_user: auto inserted user who made the request.
    Returns:
        list of rendered objects
    """
    newest_objects_list = object_manager.get_objects_by(sort='creation_time',
                                                        limit=25,
                                                        active={"$eq": True},
                                                        creation_time={'$ne': None})
    rendered_list = RenderList(newest_objects_list, request_user).render_result_list()
    if len(rendered_list) < 1:
        return make_response(rendered_list, 204)
    return make_response(rendered_list)


@object_blueprint.route('/latest', methods=['GET'])
@object_blueprint.route('/latest/', methods=['GET'])
@login_required
@insert_request_user
@right_required('base.framework.object.view')
def get_latest(request_user: User):
    """
    get object with newest last edit time
    Args:
        request_user: auto inserted user who made the request.
    Returns:
        list of rendered objects
    """
    last_objects_list = object_manager.get_objects_by(sort='last_edit_time',
                                                      limit=25,
                                                      active={"$eq": True},
                                                      last_edit_time={'$ne': None})
    rendered_list = RenderList(last_objects_list, request_user).render_result_list()
    if len(rendered_list) < 1:
        return make_response(rendered_list, 204)
    return make_response(rendered_list)


def _build_query(args, q_operator='$and'):
    query_list = []
    try:
        for key, value in args.items():
            for v in value.split(","):
                try:
                    query_list.append({key: int(v)})
                except (ValueError, TypeError):
                    return abort(400)
        return {q_operator: query_list}

    except CMDBError:
        pass
