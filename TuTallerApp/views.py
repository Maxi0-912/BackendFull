import datetime
import logging
from decimal import Decimal
from django.contrib.auth import authenticate
from django.conf import settings
from django.db.models import Avg, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Rol, Usuario, TipoEstablecimiento, Establecimiento,
    TipoServicio, Servicio, Vehiculo,
    Cita, Calificacion, Notificacion, Anuncio, PagoPendiente,
)
from .serializers import (
    RolSerializer, RegisterSerializer, UpdateUsuarioSerializer, UsuarioAdminSerializer,
    TipoEstablecimientoSerializer, TipoServicioSerializer,
    EstablecimientoSerializer, VehiculoSerializer, VehiculoAdminSerializer,
    ServicioSerializer, CitaAdminSerializer,
    CitaCreateSerializer, CitaResponseSerializer, EmpresaCitaSerializer,
    CalificacionSerializer, CalificacionAdminSerializer,
    NotificacionSerializer, NotificacionAdminSerializer,
    AnuncioSerializer, EmpresaAnuncioSerializer,
)
from .permissions import EsEmpresa, EsAdmin

logger = logging.getLogger(__name__)


def _user_data(user, request=None):
    foto_url = None
    if user.foto:
        foto_url = request.build_absolute_uri(user.foto.url) if request else user.foto.url
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'telefono': user.telefono,
        'foto': foto_url,
        'foto_url': foto_url,
        'rol': user.rol_id,
        'rol_nombre': user.rol.nombre if user.rol else None,
    }


def _auth_response(user, request=None):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'rol_nombre': user.rol.nombre if user.rol else None,
        'user': _user_data(user, request),
    }


def _not_found(msg='No encontrado'):
    return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)


# ==============================
# AUTH
# ==============================

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is None:
            try:
                u = Usuario.objects.get(email=username)
                user = authenticate(request, username=u.username, password=password)
            except Usuario.DoesNotExist:
                pass
        if user is None:
            return Response({'error': 'Credenciales invalidas'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(_auth_response(user, request))


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token_str = request.data.get('idToken') or request.data.get('id_token', '')
        if not id_token_str:
            return Response({'error': 'idToken requerido'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
            idinfo = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as e:
            logger.error(f"Google token rechazado: {e}")
            return Response({'error': 'Token de Google invalido'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error inesperado validando token de Google: {type(e).__name__}: {e}")
            return Response({'error': 'Token de Google invalido'},
                            status=status.HTTP_400_BAD_REQUEST)

        google_id  = idinfo['sub']
        email      = idinfo.get('email', '')
        first_name = idinfo.get('given_name', '')
        last_name  = idinfo.get('family_name', '')

        user = Usuario.objects.filter(google_id=google_id).first()
        if not user and email:
            user = Usuario.objects.filter(email=email).first()
        if not user:
            base = email.split('@')[0] if email else f'user{google_id[:8]}'
            username = base
            counter = 1
            while Usuario.objects.filter(username=username).exists():
                username = f'{base}{counter}'
                counter += 1
            rol_cliente = Rol.objects.filter(nombre__iexact='cliente').first()
            user = Usuario.objects.create_user(
                username=username, email=email,
                first_name=first_name, last_name=last_name,
                google_id=google_id,
            )
            if rol_cliente:
                user.rol = rol_cliente
                user.save(update_fields=['rol'])
        elif not user.google_id:
            user.google_id = google_id
            user.save(update_fields=['google_id'])

        return Response(_auth_response(user, request))


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(_auth_response(user, request), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PerfilView(APIView):
    def get(self, request):
        user = request.user
        data = _user_data(user, request)
        data['rol_nombre'] = user.rol.nombre if user.rol else None
        return Response(data)


class ActualizarPerfilView(APIView):
    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)

    def _update(self, request):
        s = UpdateUsuarioSerializer(request.user, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            request.user.refresh_from_db()
            return Response(_user_data(request.user, request))
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class EliminarCuentaView(APIView):
    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# VEHICULOS
# ==============================

class MisVehiculosView(APIView):
    def get(self, request):
        qs = Vehiculo.objects.filter(usuario=request.user)
        return Response(VehiculoSerializer(qs, many=True).data)


class CrearVehiculoView(APIView):
    def post(self, request):
        s = VehiculoSerializer(data=request.data)
        if s.is_valid():
            s.save(usuario=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class EliminarVehiculoView(APIView):
    def delete(self, request, placa):
        try:
            v = Vehiculo.objects.get(placa=placa, usuario=request.user)
        except Vehiculo.DoesNotExist:
            return _not_found()
        v.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ESTABLECIMIENTOS
# ==============================

class ListaEstablecimientosView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        qs = Establecimiento.objects.select_related('tipo', 'propietario').all()
        return Response(EstablecimientoSerializer(qs, many=True, context={'request': request}).data)


class DetalleEstablecimientoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            est = Establecimiento.objects.select_related('tipo', 'propietario').get(pk=pk)
        except Establecimiento.DoesNotExist:
            return _not_found()
        return Response(EstablecimientoSerializer(est, context={'request': request}).data)


class ResenasEstablecimientoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        qs = Calificacion.objects.filter(
            cita__establecimiento_id=pk
        ).select_related('cita__usuario')
        return Response(CalificacionSerializer(qs, many=True, context={'request': request}).data)


class CitasOcupadasView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        qs = Cita.objects.filter(
            establecimiento_id=pk,
            estado__in=['pendiente', 'confirmada'],
        )
        fecha = request.query_params.get('fecha')
        mes   = request.query_params.get('mes')
        anio  = request.query_params.get('anio')

        if fecha:
            horas = list(qs.filter(fecha=fecha).values_list('hora', flat=True))
            return Response(horas)
        elif mes and anio:
            qs = qs.filter(fecha__month=int(mes), fecha__year=int(anio))
            result = [{'fecha': str(c.fecha), 'agenda__hora': c.hora} for c in qs]
            return Response(result)
        else:
            return Response(list(qs.values_list('hora', flat=True)))


class CrearEstablecimientoView(APIView):
    def post(self, request):
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if 'lat' in data and 'latitud' not in data:
            data['latitud'] = data.pop('lat')
        if 'lng' in data and 'longitud' not in data:
            data['longitud'] = data.pop('lng')
        s = EstablecimientoSerializer(data=data, context={'request': request})
        if s.is_valid():
            s.save(propietario=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


# ==============================
# TIPOS PUBLICOS
# ==============================

class RolesPublicosView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(RolSerializer(Rol.objects.all(), many=True).data)


class TiposEstablecimientoView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(TipoEstablecimientoSerializer(TipoEstablecimiento.objects.all(), many=True).data)


class TiposServicioView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response(TipoServicioSerializer(TipoServicio.objects.all(), many=True).data)


class CrearTipoServicioView(APIView):
    def post(self, request):
        s = TipoServicioSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class AnunciosPublicosView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        today = datetime.date.today()
        qs = Anuncio.objects.filter(activo=True, estado='aprobado').filter(
            Q(es_pago=False) | Q(pagado=True)
        ).filter(
            Q(fecha_inicio__isnull=True) | Q(fecha_inicio__lte=today)
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=today)
        )
        categoria = request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria__iexact=categoria)
        ubicacion = request.query_params.get('ubicacion')
        if ubicacion:
            qs = qs.filter(ubicaciones__contains=[ubicacion])
        # Mantener en sync con _accion_de_anuncio() en serializers.py.
        accion = request.query_params.get('accion')
        if accion == 'agendar':
            qs = qs.filter(servicio__isnull=False)
        elif accion == 'enlace':
            qs = qs.filter(servicio__isnull=True).exclude(url_boton='')
        elif accion == 'ninguno':
            qs = qs.filter(servicio__isnull=True, url_boton='')
        establecimiento_id = request.query_params.get('establecimiento') or request.query_params.get('establecimiento_id')
        if establecimiento_id and establecimiento_id.isdigit():
            qs = qs.filter(establecimiento_id=establecimiento_id)
        qs = qs.order_by('orden', '-creado_en')
        return Response(AnuncioSerializer(qs, many=True, context={'request': request}).data)


# ==============================
# SERVICIOS
# ==============================

class ServiciosPorEstablecimientoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        qs = Servicio.objects.filter(
            establecimiento_id=pk
        ).select_related('tipo_servicio', 'establecimiento')
        return Response(ServicioSerializer(qs, many=True).data)


# ==============================
# CITAS
# ==============================

class MisCitasView(APIView):
    def get(self, request):
        qs = Cita.objects.filter(usuario=request.user).select_related(
            'establecimiento', 'servicio', 'vehiculo'
        ).prefetch_related('calificacion').order_by('-fecha', '-hora')
        return Response(CitaResponseSerializer(qs, many=True).data)


def _resolver_anuncio_origen(anuncio_id, establecimiento_id):
    if not anuncio_id:
        return None
    try:
        anuncio = Anuncio.objects.get(pk=anuncio_id)
    except (Anuncio.DoesNotExist, ValueError, TypeError):
        return None
    try:
        if int(anuncio.establecimiento_id) != int(establecimiento_id):
            return None
    except (TypeError, ValueError):
        return None
    if anuncio.estado != 'aprobado':
        return None
    hoy = datetime.date.today()
    if anuncio.fecha_inicio and anuncio.fecha_inicio > hoy:
        return None
    if anuncio.fecha_fin and anuncio.fecha_fin < hoy:
        return None
    return anuncio


class CrearCitaView(APIView):
    def post(self, request):
        data = request.data
        placa = str(data.get('placa', '') or '').strip().upper()
        vehiculo = None
        if placa:
            vehiculo, _ = Vehiculo.objects.get_or_create(
                placa=placa,
                defaults={'usuario': request.user, 'marca': '', 'modelo': '', 'tipo': 'carro'},
            )
        anuncio_origen = _resolver_anuncio_origen(
            data.get('anuncio_origen_id') or data.get('anuncio_origen'),
            data.get('establecimiento'),
        )
        try:
            cita = Cita.objects.create(
                usuario=request.user,
                establecimiento_id=data.get('establecimiento'),
                servicio_id=data.get('servicio') or None,
                vehiculo=vehiculo,
                anuncio_origen=anuncio_origen,
                fecha=data.get('fecha'),
                hora=data.get('hora'),
                descripcion=data.get('descripcion', '') or '',
                servicio_texto=data.get('servicio_texto', '') or '',
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            nombre_cliente = request.user.get_full_name() or request.user.username
            Notificacion.objects.create(
                usuario=cita.establecimiento.propietario,
                titulo='Nueva cita',
                mensaje=f'{nombre_cliente} agendó una cita para el {cita.fecha} a las {cita.hora}',
            )
        except Exception:
            pass
        return Response(CitaResponseSerializer(cita).data, status=status.HTTP_201_CREATED)


class DetalleCitaView(APIView):
    def get(self, request, pk):
        try:
            cita = Cita.objects.select_related(
                'establecimiento', 'servicio', 'vehiculo'
            ).get(pk=pk, usuario=request.user)
        except Cita.DoesNotExist:
            return _not_found('Cita no encontrada')
        return Response(CitaResponseSerializer(cita).data)

    def delete(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk, usuario=request.user)
        except Cita.DoesNotExist:
            return _not_found('Cita no encontrada')
        cita.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EditarCitaView(APIView):
    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)

    def _update(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk, usuario=request.user)
        except Cita.DoesNotExist:
            return _not_found('Cita no encontrada')
        data = request.data
        for field in ['fecha', 'hora', 'descripcion']:
            if field in data:
                setattr(cita, field, data[field])
        if 'establecimiento' in data:
            cita.establecimiento_id = data['establecimiento']
        if 'servicio' in data:
            cita.servicio_id = data['servicio'] or None
        placa = str(data.get('placa', '') or '').strip().upper()
        if placa:
            vehiculo, _ = Vehiculo.objects.get_or_create(
                placa=placa,
                defaults={'usuario': request.user, 'marca': '', 'modelo': '', 'tipo': 'carro'},
            )
            cita.vehiculo = vehiculo
        cita.save()
        return Response(CitaResponseSerializer(cita).data)


class EliminarCitaView(APIView):
    def delete(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk, usuario=request.user)
        except Cita.DoesNotExist:
            return _not_found('Cita no encontrada')
        cita.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CambiarEstadoCitaView(APIView):
    def patch(self, request, pk):
        try:
            cita = Cita.objects.select_related('establecimiento').get(pk=pk)
        except Cita.DoesNotExist:
            return _not_found('Cita no encontrada')
        is_owner   = cita.usuario == request.user
        is_empresa = cita.establecimiento.propietario == request.user
        if not (is_owner or is_empresa):
            return Response({'error': 'Sin permiso'}, status=status.HTTP_403_FORBIDDEN)
        nuevo_estado = request.data.get('estado')
        if not nuevo_estado:
            return Response({'error': 'estado requerido'}, status=status.HTTP_400_BAD_REQUEST)
        estado_anterior = cita.estado
        cita.estado = nuevo_estado
        cita.save(update_fields=['estado'])
        if nuevo_estado != estado_anterior:
            try:
                if nuevo_estado == 'confirmada':
                    Notificacion.objects.create(
                        usuario=cita.usuario,
                        titulo='Cita confirmada',
                        mensaje=f'Tu cita del {cita.fecha} fue confirmada',
                    )
                elif nuevo_estado == 'finalizada':
                    Notificacion.objects.create(
                        usuario=cita.usuario,
                        titulo='Servicio finalizado',
                        mensaje='Tu servicio ha sido marcado como finalizado. ¡Déjanos tu reseña!',
                    )
                elif nuevo_estado == 'cancelada':
                    if is_owner:
                        Notificacion.objects.create(
                            usuario=cita.establecimiento.propietario,
                            titulo='Cita cancelada',
                            mensaje=f'La cita del {cita.fecha} fue cancelada',
                        )
                    else:
                        Notificacion.objects.create(
                            usuario=cita.usuario,
                            titulo='Cita cancelada',
                            mensaje=f'La cita del {cita.fecha} fue cancelada',
                        )
            except Exception:
                pass
        return Response(CitaResponseSerializer(cita).data)


class AgregarComentarioEmpresaView(APIView):
    def patch(self, request, pk):
        try:
            cita = Cita.objects.get(pk=pk, establecimiento__propietario=request.user)
        except Cita.DoesNotExist:
            return _not_found('Cita no encontrada')
        nuevo_comentario  = request.data.get('comentario_empresa', '')
        comentario_previo = cita.comentario_empresa or ''
        cita.comentario_empresa = nuevo_comentario
        cita.save(update_fields=['comentario_empresa'])
        if nuevo_comentario and nuevo_comentario != comentario_previo:
            try:
                Notificacion.objects.create(
                    usuario=cita.usuario,
                    titulo='Nuevo comentario',
                    mensaje=f'La empresa dejó un comentario en tu cita del {cita.fecha}',
                )
            except Exception:
                pass
        return Response(CitaResponseSerializer(cita).data)


# ==============================
# CALIFICACIONES
# ==============================

class CrearCalificacionView(APIView):
    def post(self, request):
        cita_id = request.data.get('prestacion') or request.data.get('cita')
        try:
            cita = Cita.objects.get(pk=cita_id, usuario=request.user)
        except (Cita.DoesNotExist, ValueError, TypeError):
            return _not_found('Cita no encontrada')
        if hasattr(cita, 'calificacion'):
            return Response({'error': 'Ya existe una resena'}, status=status.HTTP_400_BAD_REQUEST)
        s = CalificacionSerializer(data=request.data)
        if s.is_valid():
            calificacion = s.save(cita=cita)
            try:
                Notificacion.objects.create(
                    usuario=cita.establecimiento.propietario,
                    titulo='Nueva reseña',
                    mensaje=f'Recibiste una calificación de {calificacion.puntuacion} estrellas',
                )
            except Exception:
                pass
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class CalificacionesPorEstablecimientoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        qs = Calificacion.objects.filter(
            cita__establecimiento_id=pk
        ).select_related('cita__usuario')
        return Response(CalificacionSerializer(qs, many=True, context={'request': request}).data)


# ==============================
# NOTIFICACIONES
# ==============================

class MisNotificacionesView(APIView):
    def get(self, request):
        qs = Notificacion.objects.filter(usuario=request.user).order_by('-fecha')
        return Response(NotificacionSerializer(qs, many=True).data)


class MarcarLeidaView(APIView):
    def patch(self, request, pk):
        try:
            notif = Notificacion.objects.get(pk=pk, usuario=request.user)
        except Notificacion.DoesNotExist:
            return _not_found()
        notif.leida = True
        notif.save(update_fields=['leida'])
        return Response({'detail': 'OK'})


# ==============================
# EMPRESA
# ==============================

class DashboardEmpresaView(APIView):
    def get(self, request):
        today          = datetime.date.today()
        first_of_month = today.replace(day=1)
        establecimientos = Establecimiento.objects.filter(propietario=request.user)
        citas_totales    = Cita.objects.filter(establecimiento__propietario=request.user)

        response = {
            'total_citas':       citas_totales.count(),
            'citas_pendientes':  citas_totales.filter(estado='pendiente').count(),
            'citas_confirmadas': citas_totales.filter(estado='confirmada').count(),
            'citas_finalizadas': citas_totales.filter(estado='finalizada').count(),
            'citas_canceladas':  citas_totales.filter(estado='cancelada').count(),
        }

        avg_cal = Calificacion.objects.filter(
            cita__establecimiento__propietario=request.user
        ).aggregate(Avg('puntuacion'))['puntuacion__avg']

        response['resumen_general'] = {
            'total_establecimientos': establecimientos.count(),
            'total_citas_mes':        citas_totales.filter(fecha__gte=first_of_month).count(),
            'pendientes_hoy':         citas_totales.filter(fecha=today, estado='pendiente').count(),
            'calificacion_promedio':  round(avg_cal, 1) if avg_cal else 0.0,
        }

        por_est = []
        for est in establecimientos:
            est_citas = Cita.objects.filter(establecimiento=est)
            est_avg   = Calificacion.objects.filter(
                cita__establecimiento=est
            ).aggregate(Avg('puntuacion'))['puntuacion__avg']
            foto_url = None
            if est.foto:
                try:
                    foto_url = request.build_absolute_uri(est.foto.url)
                except Exception:
                    foto_url = str(est.foto)
            por_est.append({
                'id':               est.id,
                'nombre':           est.nombre,
                'tipo':             est.tipo.nombre if est.tipo else '',
                'foto_url':         foto_url,
                'calificacion':     round(est_avg, 1) if est_avg else 0.0,
                'total_citas_mes':  est_citas.filter(fecha__gte=first_of_month).count(),
                'pendientes_hoy':   est_citas.filter(fecha=today, estado='pendiente').count(),
                'citas_por_estado': list(est_citas.values('estado').annotate(total=Count('id'))),
            })
        response['por_establecimiento'] = por_est
        return Response(response)


class MisEstablecimientosView(APIView):
    def get(self, request):
        qs = Establecimiento.objects.filter(propietario=request.user).select_related('tipo')
        return Response(EstablecimientoSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        s = EstablecimientoSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            s.save(propietario=request.user)
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class MiEstablecimientoDetailView(APIView):
    def _get(self, pk, user):
        try:
            return Establecimiento.objects.get(pk=pk, propietario=user)
        except Establecimiento.DoesNotExist:
            return None

    def patch(self, request, pk):
        est = self._get(pk, request.user)
        if not est:
            return _not_found()
        s = EstablecimientoSerializer(est, data=request.data, partial=True, context={'request': request})
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        est = self._get(pk, request.user)
        if not est:
            return _not_found()
        est.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmpresaCitasView(APIView):
    def get(self, request):
        qs = Cita.objects.filter(
            establecimiento__propietario=request.user
        ).select_related(
            'establecimiento', 'servicio', 'vehiculo', 'usuario', 'anuncio_origen'
        ).order_by('-fecha', '-hora')
        return Response(EmpresaCitaSerializer(qs, many=True).data)


class EmpresaServiciosView(APIView):
    def get(self, request):
        ids = Establecimiento.objects.filter(propietario=request.user).values_list('id', flat=True)
        qs  = Servicio.objects.filter(
            establecimiento_id__in=ids
        ).select_related('tipo_servicio', 'establecimiento')
        return Response(ServicioSerializer(qs, many=True).data)

    def post(self, request):
        est_id = request.data.get('establecimiento')
        if not Establecimiento.objects.filter(pk=est_id, propietario=request.user).exists():
            return Response({'error': 'Sin permiso'}, status=status.HTTP_403_FORBIDDEN)
        s = ServicioSerializer(data=request.data)
        if s.is_valid():
            s.save()
            return Response(s.data, status=status.HTTP_201_CREATED)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class EmpresaServicioDetailView(APIView):
    def _get(self, pk, user):
        try:
            return Servicio.objects.get(pk=pk, establecimiento__propietario=user)
        except Servicio.DoesNotExist:
            return None

    def patch(self, request, pk):
        sv = self._get(pk, request.user)
        if not sv:
            return _not_found()
        s = ServicioSerializer(sv, data=request.data, partial=True)
        if s.is_valid():
            s.save()
            return Response(s.data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        sv = self._get(pk, request.user)
        if not sv:
            return _not_found()
        sv.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmpresaAnunciosView(APIView):
    permission_classes = [EsEmpresa]

    def get(self, request):
        ids = Establecimiento.objects.filter(propietario=request.user).values_list('id', flat=True)
        qs = Anuncio.objects.filter(establecimiento_id__in=ids).select_related('establecimiento').annotate(
            citas_generadas_count=Count('citas_generadas')
        )
        return Response(EmpresaAnuncioSerializer(qs, many=True, context={'request': request}).data)

    def post(self, request):
        s = EmpresaAnuncioSerializer(data=request.data, context={'request': request})
        if s.is_valid():
            establecimiento = s.validated_data.get('establecimiento')
            if establecimiento is None:
                return Response({'error': 'establecimiento requerido'}, status=status.HTTP_400_BAD_REQUEST)
            ubicaciones = s.validated_data.get('ubicaciones') or []
            if 'banner' in ubicaciones:
                es_pago = True
            else:
                total = Anuncio.objects.filter(
                    establecimiento=establecimiento, ubicaciones=['perfil']
                ).count()
                es_pago = total >= Anuncio.CUPO_GRATIS
            anuncio = s.save(estado='pendiente', motivo_rechazo='', es_pago=es_pago, pagado=False)
            return Response(
                EmpresaAnuncioSerializer(anuncio, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


class EmpresaAnuncioDetailView(APIView):
    permission_classes = [EsEmpresa]

    def _get(self, pk, user):
        try:
            return Anuncio.objects.get(pk=pk, establecimiento__propietario=user)
        except Anuncio.DoesNotExist:
            return None

    def patch(self, request, pk):
        anuncio = self._get(pk, request.user)
        if not anuncio:
            return _not_found()
        s = EmpresaAnuncioSerializer(anuncio, data=request.data, partial=True, context={'request': request})
        if s.is_valid():
            s.save(estado='pendiente', motivo_rechazo='')
            return Response(EmpresaAnuncioSerializer(anuncio, context={'request': request}).data)
        return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        anuncio = self._get(pk, request.user)
        if not anuncio:
            return _not_found()
        anuncio.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmpresaAnuncioPagoView(APIView):
    permission_classes = [EsEmpresa]

    def _get_anuncio(self, pk, user):
        try:
            return Anuncio.objects.get(pk=pk, establecimiento__propietario=user)
        except Anuncio.DoesNotExist:
            return None

    def _data(self, pago):
        return {
            'referencia': pago.referencia,
            'monto': pago.monto,
            'numero_nequi': pago.numero_nequi,
            'titular': settings.NEQUI_TITULAR,
            'estado': pago.estado,
        }

    def post(self, request, pk):
        anuncio = self._get_anuncio(pk, request.user)
        if not anuncio:
            return _not_found()
        if not (anuncio.es_pago and not anuncio.pagado):
            return Response(
                {'error': 'Este anuncio no requiere pago o ya fue pagado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pago, creado = PagoPendiente.objects.get_or_create(
            anuncio=anuncio,
            defaults={
                'monto': Decimal(settings.ANUNCIO_MONTO_COP).quantize(Decimal('0.01')),
                'numero_nequi': settings.NEQUI_NUMERO,
            },
        )
        return Response(
            self._data(pago),
            status=status.HTTP_201_CREATED if creado else status.HTTP_200_OK,
        )

    def get(self, request, pk):
        anuncio = self._get_anuncio(pk, request.user)
        if not anuncio:
            return _not_found()
        try:
            pago = anuncio.pago_pendiente
        except PagoPendiente.DoesNotExist:
            return _not_found('Aun no se inicio el pago para este anuncio.')
        return Response(self._data(pago))


class EmpresaAnuncioCupoView(APIView):
    permission_classes = [EsEmpresa]

    def get(self, request):
        establecimientos = Establecimiento.objects.filter(propietario=request.user)
        data = []
        for est in establecimientos:
            total = Anuncio.objects.filter(establecimiento=est).count()
            data.append({
                'establecimiento': est.id,
                'establecimiento_nombre': est.nombre,
                'total_anuncios': total,
                'cupo_gratis': Anuncio.CUPO_GRATIS,
                'cupo_disponible': max(Anuncio.CUPO_GRATIS - total, 0),
                'requiere_pago': total >= Anuncio.CUPO_GRATIS,
            })
        return Response(data)


# ==============================
# ADMIN helpers
# ==============================

def _alist(qs, Ser, request):
    return Response(Ser(qs, many=True, context={'request': request}).data)


def _acreate(data, Ser, request):
    s = Ser(data=data, context={'request': request})
    if s.is_valid():
        s.save()
        return Response(s.data, status=status.HTTP_201_CREATED)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


def _aupdate(obj, data, Ser, request):
    s = Ser(obj, data=data, partial=True, context={'request': request})
    if s.is_valid():
        s.save()
        return Response(s.data)
    return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)


# ==============================
# ADMIN — Dashboard
# ==============================

class AdminDashboardView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        today          = datetime.date.today()
        first_of_month = today.replace(day=1)

        avg_cal = Calificacion.objects.aggregate(Avg('puntuacion'))['puntuacion__avg']

        mes_data = []
        for i in range(5, -1, -1):
            month = today.month - i
            year  = today.year
            while month <= 0:
                month += 12
                year  -= 1
            mes_data.append({
                'mes':   f'{year}-{month:02d}',
                'total': Cita.objects.filter(fecha__year=year, fecha__month=month).count(),
            })

        top_est = []
        for est in Establecimiento.objects.all()[:5]:
            avg = Calificacion.objects.filter(
                cita__establecimiento=est
            ).aggregate(Avg('puntuacion'))['puntuacion__avg']
            top_est.append({
                'id':          est.id,
                'nombre':      est.nombre,
                'promedio':    round(avg, 1) if avg else 0.0,
                'total_citas': Cita.objects.filter(establecimiento=est).count(),
            })

        ultimas = Cita.objects.select_related(
            'usuario', 'establecimiento', 'servicio'
        ).order_by('-creado_en')[:10]

        return Response({
            'resumen': {
                'total_usuarios':           Usuario.objects.count(),
                'total_establecimientos':   Establecimiento.objects.count(),
                'total_servicios':          Servicio.objects.count(),
                'total_prestaciones':       Cita.objects.count(),
                'total_calificaciones':     Calificacion.objects.count(),
                'total_vehiculos':          Vehiculo.objects.count(),
                'calificacion_promedio':    round(avg_cal, 1) if avg_cal else 0.0,
                'notificaciones_no_leidas': Notificacion.objects.filter(leida=False).count(),
                'nuevos_este_mes':          Usuario.objects.filter(
                    date_joined__date__gte=first_of_month
                ).count(),
            },
            'usuarios_por_rol':        list(Usuario.objects.values('rol__nombre').annotate(total=Count('id'))),
            'prestaciones_por_estado': list(Cita.objects.values('estado').annotate(total=Count('id'))),
            'prestaciones_por_mes':    mes_data,
            'top_establecimientos':    top_est,
            'ultimas_prestaciones': [{
                'id':                      c.id,
                'usuario__username':       c.usuario.username,
                'establecimiento__nombre': c.establecimiento.nombre,
                'servicio__nombre':        c.servicio.nombre if c.servicio else None,
                'fecha':                   str(c.fecha),
                'estado':                  c.estado,
            } for c in ultimas],
        })


# ==============================
# ADMIN — Usuarios
# ==============================

class AdminUsuarioListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        return _alist(Usuario.objects.select_related('rol').all(), UsuarioAdminSerializer, request)
    def post(self, request):
        return _acreate(request.data, UsuarioAdminSerializer, request)


class AdminUsuarioDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Usuario.objects.get(pk=pk)
        except Usuario.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, UsuarioAdminSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Establecimientos
# ==============================

class AdminEstablecimientoDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Establecimiento.objects.get(pk=pk)
        except Establecimiento.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, EstablecimientoSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Servicios
# ==============================

class AdminServicioListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        qs = Servicio.objects.select_related('tipo_servicio', 'establecimiento').all()
        return _alist(qs, ServicioSerializer, request)
    def post(self, request):
        return _acreate(request.data, ServicioSerializer, request)


class AdminServicioDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Servicio.objects.get(pk=pk)
        except Servicio.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, ServicioSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Prestaciones (Cita)
# ==============================

class AdminPrestacionListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        qs = Cita.objects.select_related(
            'usuario', 'establecimiento', 'servicio', 'vehiculo'
        ).all()
        return _alist(qs, CitaAdminSerializer, request)
    def post(self, request):
        return _acreate(request.data, CitaAdminSerializer, request)


class AdminPrestacionDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Cita.objects.get(pk=pk)
        except Cita.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, CitaAdminSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Calificaciones
# ==============================

class AdminCalificacionListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        qs = Calificacion.objects.select_related('cita__usuario').all()
        return _alist(qs, CalificacionAdminSerializer, request)
    def post(self, request):
        return _acreate(request.data, CalificacionAdminSerializer, request)


class AdminCalificacionDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Calificacion.objects.get(pk=pk)
        except Calificacion.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, CalificacionAdminSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Notificaciones
# ==============================

class AdminNotificacionListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        qs = Notificacion.objects.select_related('usuario').all()
        return _alist(qs, NotificacionAdminSerializer, request)
    def post(self, request):
        return _acreate(request.data, NotificacionAdminSerializer, request)


class AdminNotificacionDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Notificacion.objects.get(pk=pk)
        except Notificacion.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, NotificacionAdminSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Vehiculos
# ==============================

class AdminVehiculoListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        qs = Vehiculo.objects.select_related('usuario').all()
        return _alist(qs, VehiculoAdminSerializer, request)
    def post(self, request):
        return _acreate(request.data, VehiculoAdminSerializer, request)


class AdminVehiculoDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, placa):
        try: return Vehiculo.objects.get(placa=placa)
        except Vehiculo.DoesNotExist: return None
    def patch(self, request, placa):
        obj = self._obj(placa)
        return _aupdate(obj, request.data, VehiculoAdminSerializer, request) if obj else _not_found()
    def delete(self, request, placa):
        obj = self._obj(placa)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Roles
# ==============================

class AdminRolListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        return _alist(Rol.objects.all(), RolSerializer, request)
    def post(self, request):
        return _acreate(request.data, RolSerializer, request)


class AdminRolDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Rol.objects.get(pk=pk)
        except Rol.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, RolSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Tipos Establecimiento
# ==============================

class AdminTipoEstablecimientoListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        return _alist(TipoEstablecimiento.objects.all(), TipoEstablecimientoSerializer, request)
    def post(self, request):
        return _acreate(request.data, TipoEstablecimientoSerializer, request)


class AdminTipoEstablecimientoDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return TipoEstablecimiento.objects.get(pk=pk)
        except TipoEstablecimiento.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, TipoEstablecimientoSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Tipos Servicio
# ==============================

class AdminTipoServicioListView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        return _alist(TipoServicio.objects.all(), TipoServicioSerializer, request)
    def post(self, request):
        return _acreate(request.data, TipoServicioSerializer, request)


class AdminTipoServicioDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return TipoServicio.objects.get(pk=pk)
        except TipoServicio.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, TipoServicioSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


# ==============================
# ADMIN — Agenda (model removed — stub)
# ==============================

class AdminAgendaView(APIView):
    permission_classes = [EsAdmin]

    def get(self, request):
        return Response([])


# ==============================
# ADMIN — Anuncios
# ==============================

class AdminAnuncioListView(APIView):
    permission_classes = [EsAdmin]

    ORDERING_FIELDS = {'creado_en', '-creado_en', 'actualizado_en', '-actualizado_en'}

    def get(self, request):
        qs = Anuncio.objects.all()

        estado = request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado__iexact=estado)

        activo = request.query_params.get('activo')
        if activo is not None:
            qs = qs.filter(activo=activo.lower() in ('true', '1'))

        categoria = request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(categoria__iexact=categoria)

        establecimiento_id = request.query_params.get('establecimiento') or request.query_params.get('establecimiento_id')
        if establecimiento_id and establecimiento_id.isdigit():
            qs = qs.filter(establecimiento_id=establecimiento_id)

        ordering = request.query_params.get('ordering')
        qs = qs.order_by(ordering if ordering in self.ORDERING_FIELDS else '-creado_en')

        return _alist(qs, AnuncioSerializer, request)
    def post(self, request):
        return _acreate(request.data, AnuncioSerializer, request)


class AdminAnuncioDetailView(APIView):
    permission_classes = [EsAdmin]

    def _obj(self, pk):
        try: return Anuncio.objects.get(pk=pk)
        except Anuncio.DoesNotExist: return None
    def patch(self, request, pk):
        obj = self._obj(pk)
        return _aupdate(obj, request.data, AnuncioSerializer, request) if obj else _not_found()
    def delete(self, request, pk):
        obj = self._obj(pk)
        if not obj: return _not_found()
        obj.delete(); return Response(status=status.HTTP_204_NO_CONTENT)


class AdminAnuncioValidarView(APIView):
    permission_classes = [EsAdmin]

    def patch(self, request, pk):
        try:
            anuncio = Anuncio.objects.get(pk=pk)
        except Anuncio.DoesNotExist:
            return _not_found()
        nuevo_estado = request.data.get('estado')
        if nuevo_estado not in ('aprobado', 'rechazado'):
            return Response(
                {'error': "estado debe ser 'aprobado' o 'rechazado'"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        anuncio.estado = nuevo_estado
        anuncio.motivo_rechazo = request.data.get('motivo_rechazo', '') if nuevo_estado == 'rechazado' else ''
        anuncio.save(update_fields=['estado', 'motivo_rechazo', 'actualizado_en'])
        return Response(AnuncioSerializer(anuncio, context={'request': request}).data)
