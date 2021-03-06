# DATAGERRY - OpenSource Enterprise CMDB
# Copyright (C) 2019 - 2021 NETHINKS GmbH
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
# along with this program. If not, see <https://www.gnu.org/licenses/>.
from typing import Union, List

from bson import Regex

from cmdb.database.managers import DatabaseManagerMongo
from cmdb.framework import CmdbObject
from cmdb.framework.cmdb_object_manager import verify_access
from cmdb.manager.managers import ManagerQueryBuilder, ManagerBase
from cmdb.framework.managers.type_manager import TypeManager
from cmdb.framework.results import IterationResult
from cmdb.framework.utils import PublicID
from cmdb.manager import ManagerGetError, ManagerIterationError
from cmdb.search import Query, Pipeline
from cmdb.security.acl.builder import AccessControlQueryBuilder
from cmdb.security.acl.permission import AccessControlPermission
from cmdb.user_management import UserModel


class ObjectQueryBuilder(ManagerQueryBuilder):

    def __init__(self):
        super(ObjectQueryBuilder, self).__init__()

    def build(self, filter: Union[List[dict], dict], limit: int, skip: int, sort: str, order: int,
              user: UserModel = None, permission: AccessControlPermission = None, *args, **kwargs) -> \
            Union[Query, Pipeline]:
        """
        Converts the parameters from the call to a mongodb aggregation pipeline
        Args:
            filter: dict or list of dict query/queries which the elements have to match.
            limit: max number of documents to return.
            skip: number of documents to skip first.
            sort: sort field
            order: sort order
            user: request user
            permission: AccessControlPermission
            *args:
            **kwargs:

        Returns:
            The `FrameworkQueryBuilder` query pipeline with the parameter contents.
        """
        self.clear()
        self.query = Pipeline([])

        if isinstance(filter, dict):
            self.query.append(self.match_(filter))
        elif isinstance(filter, list):
            for pipe in filter:
                self.query.append(pipe)

        if user and permission:
            self.query += (AccessControlQueryBuilder().build(group_id=PublicID(user.group_id), permission=permission))

        if limit == 0:
            results_query = [self.skip_(limit)]
        else:
            results_query = [self.skip_(skip), self.limit_(limit)]

        # TODO: Remove nasty quick hack
        if sort.startswith('fields'):
            sort_value = sort[7:]
            self.query.append({'$addFields': {
                'order': {
                    '$filter': {
                        'input': '$fields',
                        'as': 'fields',
                        'cond': {'$eq': ['$$fields.name', sort_value]}
                    }
                }
            }})
            self.query.append({'$sort': {'order': order}})
        else:
            self.query.append(self.sort_(sort=sort, order=order))

        self.query += results_query
        return self.query

    def count(self, filter: Union[List[dict], dict], user: UserModel = None,
              permission: AccessControlPermission = None) -> Union[Query, Pipeline]:
        """
        Count the number of documents in the stages
        Args:
            filter: filter requirement
            user: request user
            permission: acl permission

        Returns:
            Query with count stages.
        """
        self.clear()
        self.query = Pipeline([])

        if isinstance(filter, dict):
            self.query.append(self.match_(filter))
        elif isinstance(filter, list):
            for pipe in filter:
                self.query.append(pipe)

        if user and permission:
            self.query += (AccessControlQueryBuilder().build(group_id=PublicID(user.group_id), permission=permission))

        self.query.append(self.count_('total'))
        return self.query


class ObjectManager(ManagerBase):

    def __init__(self, database_manager: DatabaseManagerMongo):
        self.object_builder = ObjectQueryBuilder()
        super(ObjectManager, self).__init__(CmdbObject.COLLECTION, database_manager=database_manager)

    def get(self, public_id: Union[PublicID, int], user: UserModel = None,
            permission: AccessControlPermission = None) -> CmdbObject:
        """
        Get a single object by its id.

        Args:
            public_id (int): ID of the object.
            user: Request user
            permission: ACL permission

        Returns:
            CmdbObject: Instance of CmdbObject with data.
        """
        cursor_result = self._get(self.collection, filter={'public_id': public_id}, limit=1)
        for resource_result in cursor_result.limit(-1):
            resource = CmdbObject.from_data(resource_result)
            type_ = TypeManager(database_manager=self._database_manager).get(resource.type_id)
            verify_access(type_, user, permission)
            return resource
        else:
            raise ManagerGetError(f'Object with ID: {public_id} not found!')

    def iterate(self, filter: Union[List[dict], dict], limit: int, skip: int, sort: str, order: int,
                user: UserModel = None, permission: AccessControlPermission = None, *args, **kwargs) \
            -> IterationResult[CmdbObject]:
        try:
            query: Pipeline = self.object_builder.build(filter=filter, limit=limit, skip=skip, sort=sort, order=order,
                                                        user=user, permission=permission)
            count_query: Pipeline = self.object_builder.count(filter=filter, user=user, permission=permission)
            aggregation_result = list(self._aggregate(self.collection, query))
            total_cursor = self._aggregate(self.collection, count_query)
            total = 0
            while total_cursor.alive:
                total = next(total_cursor)['total']
        except ManagerGetError as err:
            raise ManagerIterationError(err=err)
        iteration_result: IterationResult[CmdbObject] = IterationResult(aggregation_result, total)
        iteration_result.convert_to(CmdbObject)
        return iteration_result

    def references(self, object_: CmdbObject, filter: dict, limit: int, skip: int, sort: str, order: int,
                   user: UserModel = None, permission: AccessControlPermission = None, *args, **kwargs) \
            -> IterationResult[CmdbObject]:
        query = []
        if isinstance(filter, dict):
            query.append(filter)
        elif isinstance(filter, list):
            query += filter
        query.append({
            '$lookup': {
                'from': 'framework.types',
                'localField': 'type_id',
                'foreignField': 'public_id',
                'as': 'type'
            }
        })
        query.append({
            '$unwind': {
                'path': '$type'
            }
        })
        query.append({
            '$match': {
                'type.fields.type': 'ref',
                '$or': [
                    {'type.fields.ref_types': Regex(f'.*{object_.type_id}.*', 'i')},
                    {'type.fields.ref_types': object_.type_id}
                ]
            }
        })
        query.append({
            '$match': {
                'fields.value': object_.public_id
            }
        })
        return self.iterate(filter=query, limit=limit, skip=skip, sort=sort, order=order,
                            user=user, permission=permission)
