import uuid

import pytest
from freezegun import freeze_time

from app import notify_celery


# requiring app ensures notify_celery.init_app has been called
@pytest.fixture(scope='session')
def celery_task(notify_ftp):
    @notify_celery.task(name=uuid.uuid4(), base=notify_celery.task_cls)
    def test_task(delivery_info=None):
        pass

    return test_task


@pytest.fixture
def async_task(celery_task):
    celery_task.push_request(delivery_info={'routing_key': 'test-queue'})
    yield celery_task
    celery_task.pop_request()


def test_success_should_log_and_call_statsd(mocker, notify_ftp, async_task):
    statsd = mocker.patch.object(notify_ftp.statsd_client, 'timing')
    logger = mocker.patch.object(notify_ftp.logger, 'info')

    with freeze_time() as frozen:
        async_task()
        frozen.tick(5)

        async_task.on_success(
            retval=None, task_id=1234, args=[], kwargs={}
        )

    statsd.assert_called_once_with(f'celery.test-queue.{async_task.name}.success', 5.0)
    logger.assert_called_once_with(f'Celery task {async_task.name} (queue: test-queue) took 5.0000')


def test_success_queue_when_applied_synchronously(mocker, notify_ftp, celery_task):
    statsd = mocker.patch.object(notify_ftp.statsd_client, 'timing')
    logger = mocker.patch.object(notify_ftp.logger, 'info')

    with freeze_time() as frozen:
        celery_task()
        frozen.tick(5)

        celery_task.on_success(
            retval=None, task_id=1234, args=[], kwargs={}
        )

    statsd.assert_called_once_with(f'celery.none.{celery_task.name}.success', 5.0)
    logger.assert_called_once_with(f'Celery task {celery_task.name} (queue: none) took 5.0000')


def test_failure_should_log_and_call_statsd(mocker, notify_ftp, async_task):
    statsd = mocker.patch.object(notify_ftp.statsd_client, 'incr')
    logger = mocker.patch.object(notify_ftp.logger, 'exception')

    async_task.on_failure(
        exc=Exception, task_id=1234, args=[], kwargs={}, einfo=None
    )

    statsd.assert_called_once_with(f'celery.test-queue.{async_task.name}.failure')
    logger.assert_called_once_with(f'Celery task {async_task.name} (queue: test-queue) failed')


def test_failure_queue_when_applied_synchronously(mocker, notify_ftp, celery_task):
    statsd = mocker.patch.object(notify_ftp.statsd_client, 'incr')
    logger = mocker.patch.object(notify_ftp.logger, 'exception')

    celery_task.on_failure(
        exc=Exception, task_id=1234, args=[], kwargs={}, einfo=None
    )

    statsd.assert_called_once_with(f'celery.none.{celery_task.name}.failure')
    logger.assert_called_once_with(f'Celery task {celery_task.name} (queue: none) failed')


def test_call_exports_request_id_from_kwargs(mocker, celery_task):
    g = mocker.patch('app.celery.celery.g')
    # this would fail if the kwarg was passed through unexpectedly
    celery_task(request_id='1234')
    assert g.request_id == '1234'
