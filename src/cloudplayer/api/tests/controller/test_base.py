import mock
import pytest
import sqlalchemy.orm.util

from cloudplayer.api.access import Fields
from cloudplayer.api.controller.base import Controller, ControllerException
from cloudplayer.api.model.account import Account


def test_controller_should_store_creation_args(db, current_user):
    controller = Controller(db, current_user)
    assert controller.db is db
    assert controller.current_user is current_user


def test_controller_should_merge_ids_into_keywords():
    ids = {'a': 1, 'b': 2}
    kw = {'c': 3, 'd': 4}
    params = Controller._merge_ids_with_kw(ids, kw)
    assert params == {'a': 1, 'b': 2, 'c': 3, 'd': 4}


def test_controller_merge_should_complain_about_conflicting_fields():
    ids = {'a': 1, 'same': 'foo'}
    kw = {'b': 2, 'same': 'bar'}
    with pytest.raises(ControllerException) as error:
        Controller._merge_ids_with_kw(ids, kw)
    assert error.value.status_code == 400


def test_controller_should_eject_ids_from_keywords():
    ids = {'a': 1, 'b': 2}
    kw = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
    params = Controller._eject_ids_from_kw(ids, kw)
    assert params == {'c': 3, 'd': 4}


def test_controller_eject_should_complain_about_conflicting_fields():
    ids = {'a': 1, 'same': 'foo'}
    kw = {'a': 1, 'b': 2, 'same': 'bar'}
    with pytest.raises(ControllerException) as error:
        Controller._eject_ids_from_kw(ids, kw)
    assert error.value.status_code == 400


class MyController(Controller):

    def __init__(self, db, cu, model, policy):
        self.db = db
        self.current_user = cu
        self.__model__ = model
        self.policy = policy


@pytest.mark.gen_test
def test_controller_should_create_entity_and_read_result(
        db, current_user, account, user):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': '1234', 'provider_id': 'cloudplayer'}
    kw = {'title': 'foo', 'access_token': 'bar', 'user_id': user.id}
    entity = yield controller.create(ids, kw, Fields('id', 'title'))
    assert entity.id == '1234'
    assert entity.provider_id == 'cloudplayer'
    assert entity.title == 'foo'
    assert entity.access_token == 'bar'
    assert sqlalchemy.orm.util.object_state(entity).persistent

    assert controller.policy.grant_create.call_args[0][:-1] == (
        account, entity)
    assert set(controller.policy.grant_create.call_args[0][-1]) == {
        'provider_id', 'title', 'title', 'access_token', 'id', 'user_id'}

    assert controller.policy.grant_read.call_args[0][:-1] == (
        account, entity)
    assert set(controller.policy.grant_read.call_args[0][-1]) == {
        'id', 'title'}


@pytest.mark.gen_test
def test_controller_should_raise_not_found_on_failed_read(
        db, current_user):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': 'does-not-exist', 'provider_id': 'unheard-of'}
    with pytest.raises(ControllerException) as error:
        yield controller.read(ids)
    assert error.value.status_code == 404


@pytest.mark.gen_test
def test_controller_should_read_entity_by_the_books(
        db, current_user, account):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': account.id, 'provider_id': account.provider_id}
    entity = yield controller.read(ids, Fields('title', 'provider_id'))

    assert entity is account
    assert controller.policy.grant_read.call_args[0][:-1] == (
        account, entity)
    assert set(controller.policy.grant_read.call_args[0][-1]) == {
        'provider_id', 'title'}


@pytest.mark.gen_test
def test_controller_should_raise_not_found_on_failed_update(
        db, current_user):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': 'does-not-exist', 'provider_id': 'unheard-of'}
    kw = {'title': 'foo', 'refresh_token': 'bar'}
    with pytest.raises(ControllerException) as error:
        yield controller.update(ids, kw, Fields('user_id', 'title'))
    assert error.value.status_code == 404


@pytest.mark.gen_test
def test_controller_should_update_entity_and_read_result(
        db, current_user, account):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': account.id, 'provider_id': account.provider_id}
    kw = {'title': 'foo', 'refresh_token': 'bar'}
    entity = yield controller.update(ids, kw, Fields('user_id', 'title'))
    assert entity is account
    assert sqlalchemy.orm.util.object_state(entity).persistent

    assert controller.policy.grant_update.call_args[0][:-1] == (
        account, entity)
    assert set(controller.policy.grant_update.call_args[0][-1]) == {
        'title', 'refresh_token'}

    assert controller.policy.grant_read.call_args[0][:-1] == (
        account, entity)
    assert set(controller.policy.grant_read.call_args[0][-1]) == {
        'user_id', 'title'}


@pytest.mark.gen_test
def test_controller_should_raise_not_found_on_failed_delete(
        db, current_user):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': 'does-not-exist', 'provider_id': 'unheard-of'}
    with pytest.raises(ControllerException) as error:
        yield controller.delete(ids)
    assert error.value.status_code == 404


@pytest.mark.gen_test
def test_controller_should_delete_entity_and_not_return_anything(
        db, current_user, account):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': account.id, 'provider_id': account.provider_id}
    result = yield controller.delete(ids)
    assert result is None
    assert sqlalchemy.orm.util.object_state(account).was_deleted

    assert controller.policy.grant_delete.call_args[0] == (
        account, account)


@pytest.mark.gen_test
def test_controller_should_produce_model_query_with_arguments(
        db, current_user, account):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'provider_id': 'cloudplayer'}
    kw = {'title': 'foo'}
    query = yield controller.query(ids, kw)
    assert query.statement.froms[0].name == 'account'
    assert str(query.whereclause) == (
        'account.title = :title_1 AND account.provider_id = :provider_id_1')

    assert controller.policy.grant_query.call_args[0] == (
        account, Account, kw)


@pytest.mark.gen_test
def test_controller_should_search_using_query_and_read_all_entities(
        db, current_user, account):
    controller = MyController(db, current_user, Account, mock.Mock())
    ids = {'id': account.id, 'provider_id': account.provider_id}
    result = yield controller.search(ids, {}, Fields('id'))
    entity = result[0]
    assert controller.policy.grant_read.call_args[0][:-1] == (
        account, entity)
    assert set(controller.policy.grant_read.call_args[0][-1]) == {'id'}
