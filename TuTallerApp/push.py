import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_app = None
_app_intentado = False


def _get_app():
    """Inicializa Firebase una sola vez, a partir del JSON de la cuenta de
    servicio leido de una variable de entorno (nunca un archivo)."""
    global _app, _app_intentado
    if _app_intentado:
        return _app
    _app_intentado = True
    if not settings.FIREBASE_CREDENTIALS_JSON:
        logger.warning('FIREBASE_CREDENTIALS_JSON no esta configurado; push deshabilitado.')
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials

        credenciales = json.loads(settings.FIREBASE_CREDENTIALS_JSON)
        _app = firebase_admin.initialize_app(credentials.Certificate(credenciales))
    except Exception as e:
        logger.error(f'No se pudo inicializar Firebase: {type(e).__name__}: {e}')
        _app = None
    return _app


def enviar_push(usuario, titulo, cuerpo, data=None):
    """Envia una notificacion push data-only (sin bloque 'notification') a
    todos los dispositivos activos de 'usuario'. Android arma y muestra la
    notificacion por su cuenta a partir de 'data', tanto en foreground como
    en background, y usa 'tipo'/'cita_id' (u otros ids incluidos en data)
    para el deep link.

    Nunca debe tumbar la operacion que la dispara: cualquier fallo se loguea
    y se ignora.
    """
    try:
        from .models import DispositivoToken  # import diferido: evita ciclo con models.py

        app = _get_app()
        if not app:
            return

        tokens_activos = DispositivoToken.objects.filter(usuario=usuario, activo=True)
        tokens = list(tokens_activos.values_list('token', flat=True))
        if not tokens:
            return

        payload = {'titulo': titulo, 'cuerpo': cuerpo}
        if data:
            payload.update({str(k): str(v) for k, v in data.items()})

        from firebase_admin import messaging

        mensajes = [messaging.Message(data=payload, token=token) for token in tokens]
        respuesta = messaging.send_each(mensajes, app=app)

        tokens_invalidos = [
            token for token, resultado in zip(tokens, respuesta.responses)
            if not resultado.success and isinstance(resultado.exception, messaging.UnregisteredError)
        ]
        for token, resultado in zip(tokens, respuesta.responses):
            if not resultado.success and token not in tokens_invalidos:
                logger.warning(f'Push fallido para token {token[:12]}...: {resultado.exception}')

        if tokens_invalidos:
            tokens_activos.filter(token__in=tokens_invalidos).update(activo=False)
            logger.info(f'{len(tokens_invalidos)} token(s) invalido(s) desactivado(s).')

    except Exception as e:
        logger.error(f'Error inesperado enviando push a {getattr(usuario, "username", usuario)}: {type(e).__name__}: {e}')
