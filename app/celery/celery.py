from celery import Celery, Task


def make_task(app):
    class NotifyTask(Task):
        abstract = True

        def on_failure(self, exc, task_id, args, kwargs, einfo):
            # ensure task will log exceptions to correct handlers
            with app.app_context():
                app.logger.exception('Celery task failed')
                super().on_failure(exc, task_id, args, kwargs, einfo)

        def __call__(self, *args, **kwargs):
            # ensure task has flask context to access config, logger, etc
            with app.app_context():
                return super().__call__(*args, **kwargs)

    return NotifyTask


class NotifyCelery(Celery):

    def init_app(self, app):
        super().__init__(
            app.import_name,
            broker=app.config['CELERY']['broker_url'],
            task_cls=make_task(app),
        )

        self.conf.update(app.config['CELERY'])
