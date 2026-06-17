from django.apps import AppConfig


class PagosConfig(AppConfig):
    name = 'pagos'
    verbose_name = 'Gestión de Pagos'
    
    def ready(self):
        """
        Este método se ejecuta cuando Django carga la app.
        Registra los signals para procesamiento automático de matrículas.
        """
        import pagos.signals  # noqa: F401
