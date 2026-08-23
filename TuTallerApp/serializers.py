from rest_framework import serializers
from django.db.models import Avg
from .models import (
    Rol, Usuario, TipoEstablecimiento, Establecimiento, FotoEstablecimiento,
    TipoServicio, Servicio, Vehiculo, Cita, Calificacion, Notificacion, Anuncio
)


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Rol
        fields = ['id', 'nombre', 'descripcion', 'activo']


class RegisterSerializer(serializers.Serializer):
    username   = serializers.CharField()
    email      = serializers.EmailField()
    password   = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    last_name  = serializers.CharField(required=False, allow_blank=True, default='')
    telefono   = serializers.CharField(required=False, allow_blank=True, default='')
    rol        = serializers.IntegerField(required=False, allow_null=True)

    def validate_username(self, value):
        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError('El nombre de usuario ya existe.')
        return value

    def validate_email(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('El correo ya esta registrado.')
        return value

    def create(self, validated_data):
        rol_id = validated_data.pop('rol', None)
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)
        if rol_id:
            try:
                user.rol = Rol.objects.get(pk=rol_id)
            except Rol.DoesNotExist:
                pass
        user.save()
        return user


class UpdateUsuarioSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, required=False, min_length=6)
    rol       = serializers.IntegerField(required=False, allow_null=True, write_only=True)

    class Meta:
        model  = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'foto',
                  'is_active', 'password', 'rol']

    def validate_username(self, value):
        if Usuario.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('El nombre de usuario ya existe.')
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        rol_id   = validated_data.pop('rol', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        if rol_id is not None:
            try:
                instance.rol = Rol.objects.get(pk=rol_id)
            except Rol.DoesNotExist:
                pass
        instance.save()
        return instance


class UsuarioAdminSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    foto_url   = serializers.SerializerMethodField()
    password   = serializers.CharField(write_only=True, required=False)

    class Meta:
        model  = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'telefono', 'rol', 'rol_nombre', 'foto', 'foto_url',
            'is_active', 'date_joined', 'password',
        ]
        read_only_fields = ['date_joined']

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class VehiculoSerializer(serializers.ModelSerializer):
    usuario = serializers.IntegerField(source='usuario_id', read_only=True)

    class Meta:
        model  = Vehiculo
        fields = ['placa', 'usuario', 'marca', 'modelo', 'anio', 'tipo']


class VehiculoAdminSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = Vehiculo
        fields = ['placa', 'usuario', 'usuario_nombre', 'marca', 'modelo', 'anio', 'tipo']


class TipoEstablecimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoEstablecimiento
        fields = ['id', 'nombre']


class TipoServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TipoServicio
        fields = ['id', 'nombre']


class EstablecimientoSerializer(serializers.ModelSerializer):
    tipo_nombre            = serializers.CharField(source='tipo.nombre', read_only=True)
    propietario_nombre     = serializers.CharField(source='propietario.username', read_only=True)
    calificacion_promedio  = serializers.SerializerMethodField()
    foto_url               = serializers.SerializerMethodField()
    fotos_galeria          = serializers.SerializerMethodField()

    class Meta:
        model  = Establecimiento
        fields = [
            'id', 'nombre', 'direccion', 'telefono', 'descripcion',
            'hora_apertura', 'hora_cierre', 'latitud', 'longitud',
            'tipo', 'tipo_nombre', 'foto', 'foto_url', 'fotos_galeria',
            'propietario', 'propietario_nombre',
            'calificacion_promedio',
        ]
        read_only_fields = ['propietario']

    def get_calificacion_promedio(self, obj):
        avg = Calificacion.objects.filter(
            cita__establecimiento=obj
        ).aggregate(Avg('puntuacion'))['puntuacion__avg']
        return round(avg, 1) if avg else 0.0

    def get_foto_url(self, obj):
        request = self.context.get('request')
        if obj.foto and request:
            return request.build_absolute_uri(obj.foto.url)
        return None

    def get_fotos_galeria(self, obj):
        request = self.context.get('request')
        fotos = obj.fotos.all()
        if request:
            return [request.build_absolute_uri(f.imagen.url) for f in fotos if f.imagen]
        return [f.imagen.url for f in fotos if f.imagen]


class ServicioSerializer(serializers.ModelSerializer):
    tipo_servicio_nombre   = serializers.CharField(source='tipo_servicio.nombre', read_only=True)
    establecimiento_nombre = serializers.CharField(source='establecimiento.nombre', read_only=True)
    establecimiento_id     = serializers.IntegerField(source='establecimiento.id', read_only=True)
    tipo_servicio_id       = serializers.IntegerField(source='tipo_servicio.id', read_only=True)

    class Meta:
        model  = Servicio
        fields = [
            'id', 'nombre',
            'establecimiento', 'establecimiento_id', 'establecimiento_nombre',
            'tipo_servicio', 'tipo_servicio_id', 'tipo_servicio_nombre',
        ]


class CitaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Cita
        fields = [
            'establecimiento', 'servicio', 'servicio_texto',
            'vehiculo', 'fecha', 'hora', 'descripcion', 'estado',
        ]


class CitaResponseSerializer(serializers.ModelSerializer):
    establecimiento_nombre = serializers.CharField(source='establecimiento.nombre', read_only=True)
    servicio_nombre        = serializers.SerializerMethodField()
    vehiculo_placa         = serializers.SerializerMethodField()
    tiene_resena           = serializers.SerializerMethodField()

    class Meta:
        model  = Cita
        fields = [
            'id', 'fecha', 'hora', 'estado',
            'establecimiento', 'establecimiento_nombre',
            'servicio', 'servicio_nombre', 'servicio_texto',
            'vehiculo_placa', 'tiene_resena',
            'descripcion', 'comentario_empresa',
        ]

    def get_servicio_nombre(self, obj):
        return obj.servicio.nombre if obj.servicio else None

    def get_vehiculo_placa(self, obj):
        return obj.vehiculo.placa if obj.vehiculo else None

    def get_tiene_resena(self, obj):
        return hasattr(obj, 'calificacion')


class CitaAdminSerializer(serializers.ModelSerializer):
    usuario_nombre         = serializers.CharField(source='usuario.username', read_only=True)
    establecimiento_nombre = serializers.CharField(source='establecimiento.nombre', read_only=True)
    servicio_nombre        = serializers.SerializerMethodField()
    vehiculo_placa         = serializers.SerializerMethodField()

    class Meta:
        model  = Cita
        fields = [
            'id', 'usuario', 'usuario_nombre',
            'establecimiento', 'establecimiento_nombre',
            'servicio', 'servicio_nombre', 'servicio_texto',
            'vehiculo', 'vehiculo_placa',
            'fecha', 'hora', 'estado', 'descripcion', 'comentario_empresa', 'creado_en',
        ]
        read_only_fields = ['creado_en']

    def get_servicio_nombre(self, obj):
        return obj.servicio.nombre if obj.servicio else None

    def get_vehiculo_placa(self, obj):
        return obj.vehiculo.placa if obj.vehiculo else None


class EmpresaCitaSerializer(serializers.ModelSerializer):
    establecimiento_nombre = serializers.CharField(source='establecimiento.nombre', read_only=True)
    establecimiento_id     = serializers.IntegerField(source='establecimiento.id', read_only=True)
    usuario_nombre         = serializers.SerializerMethodField()
    usuario_telefono       = serializers.SerializerMethodField()
    servicio_nombre        = serializers.SerializerMethodField()
    vehiculo_placa         = serializers.SerializerMethodField()
    tiene_resena           = serializers.SerializerMethodField()

    class Meta:
        model  = Cita
        fields = [
            'id', 'fecha', 'hora', 'estado',
            'establecimiento', 'establecimiento_id', 'establecimiento_nombre',
            'usuario_nombre', 'usuario_telefono',
            'servicio', 'servicio_nombre', 'servicio_texto',
            'vehiculo_placa', 'tiene_resena',
            'descripcion', 'comentario_empresa',
        ]

    def get_usuario_nombre(self, obj):
        u = obj.usuario
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_usuario_telefono(self, obj):
        return obj.usuario.telefono

    def get_servicio_nombre(self, obj):
        return obj.servicio.nombre if obj.servicio else None

    def get_vehiculo_placa(self, obj):
        return obj.vehiculo.placa if obj.vehiculo else None

    def get_tiene_resena(self, obj):
        return hasattr(obj, 'calificacion')


class CalificacionSerializer(serializers.ModelSerializer):
    prestacion     = serializers.IntegerField(source='cita_id', read_only=True)
    usuario        = serializers.SerializerMethodField()
    usuario_nombre = serializers.SerializerMethodField()
    foto_url       = serializers.SerializerMethodField()

    class Meta:
        model  = Calificacion
        fields = ['id', 'prestacion', 'puntuacion', 'comentario', 'fecha',
                  'usuario', 'usuario_nombre', 'foto_url']
        read_only_fields = ['fecha', 'prestacion']

    def get_usuario(self, obj):
        return obj.cita.usuario.username

    def get_usuario_nombre(self, obj):
        u = obj.cita.usuario
        return f"{u.first_name} {u.last_name}".strip() or u.username

    def get_foto_url(self, obj):
        request = self.context.get('request')
        u = obj.cita.usuario
        if u.foto and request:
            return request.build_absolute_uri(u.foto.url)
        return None


class CalificacionAdminSerializer(serializers.ModelSerializer):
    prestacion     = serializers.IntegerField(source='cita_id', read_only=True)
    usuario        = serializers.SerializerMethodField()
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model  = Calificacion
        fields = ['id', 'cita', 'prestacion', 'puntuacion', 'comentario', 'fecha',
                  'usuario', 'usuario_nombre']
        read_only_fields = ['fecha', 'prestacion']

    def get_usuario(self, obj):
        return obj.cita.usuario.username

    def get_usuario_nombre(self, obj):
        u = obj.cita.usuario
        return f"{u.first_name} {u.last_name}".strip() or u.username


class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notificacion
        fields = ['id', 'usuario', 'titulo', 'mensaje', 'leida', 'fecha']


class NotificacionAdminSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model  = Notificacion
        fields = ['id', 'usuario', 'usuario_nombre', 'titulo', 'mensaje', 'leida', 'fecha']


class ServicioMinSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Servicio
        fields = ['id', 'nombre']


class AnuncioSerializer(serializers.ModelSerializer):
    imagen_url             = serializers.SerializerMethodField()
    establecimiento_nombre = serializers.CharField(source='establecimiento.nombre', read_only=True)
    servicio_detalle        = ServicioMinSerializer(source='servicio', read_only=True)

    class Meta:
        model  = Anuncio
        fields = [
            'id', 'titulo', 'descripcion', 'imagen', 'imagen_url', 'tipo',
            'categoria', 'descuento',
            'texto_boton', 'url_boton', 'establecimiento', 'establecimiento_nombre',
            'servicio', 'servicio_detalle',
            'activo', 'orden', 'fecha_inicio', 'fecha_fin',
            'estado', 'motivo_rechazo', 'es_pago', 'pagado',
            'creado_en', 'actualizado_en',
        ]

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen and request:
            return request.build_absolute_uri(obj.imagen.url)
        return None


IMAGEN_CONTENT_TYPES_VALIDAS = ('image/jpeg', 'image/png', 'image/webp')
IMAGEN_TAMANIO_MAXIMO = 3 * 1024 * 1024  # 3 MB


class EmpresaAnuncioSerializer(serializers.ModelSerializer):
    imagen_url             = serializers.SerializerMethodField()
    establecimiento_nombre = serializers.CharField(source='establecimiento.nombre', read_only=True)
    servicio_detalle        = ServicioMinSerializer(source='servicio', read_only=True)

    class Meta:
        model  = Anuncio
        fields = [
            'id', 'titulo', 'descripcion', 'imagen', 'imagen_url', 'tipo',
            'categoria', 'descuento',
            'texto_boton', 'url_boton', 'establecimiento', 'establecimiento_nombre',
            'servicio', 'servicio_detalle',
            'activo', 'orden', 'fecha_inicio', 'fecha_fin',
            'estado', 'motivo_rechazo', 'es_pago', 'pagado',
            'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['estado', 'motivo_rechazo', 'es_pago', 'pagado']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            self.fields['servicio'].queryset = Servicio.objects.filter(
                establecimiento__propietario=request.user
            )

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen and request:
            return request.build_absolute_uri(obj.imagen.url)
        return None

    def validate_establecimiento(self, value):
        request = self.context.get('request')
        if request and value.propietario_id != request.user.id:
            raise serializers.ValidationError('El establecimiento no pertenece al usuario.')
        return value

    def validate(self, attrs):
        establecimiento = attrs.get('establecimiento', getattr(self.instance, 'establecimiento', None))
        servicio = attrs.get('servicio', getattr(self.instance, 'servicio', None))
        if servicio and establecimiento and servicio.establecimiento_id != establecimiento.id:
            raise serializers.ValidationError(
                {'servicio': 'El servicio debe pertenecer al mismo establecimiento del anuncio.'}
            )
        return attrs

    def validate_url_boton(self, value):
        if value and not value.lower().startswith(('http://', 'https://')):
            raise serializers.ValidationError('La URL debe comenzar con http:// o https://.')
        return value

    def validate_imagen(self, value):
        if not value:
            return value
        content_type = getattr(value, 'content_type', None)
        if content_type and content_type not in IMAGEN_CONTENT_TYPES_VALIDAS:
            raise serializers.ValidationError('La imagen debe ser JPG, PNG o WEBP.')
        if value.size and value.size > IMAGEN_TAMANIO_MAXIMO:
            raise serializers.ValidationError('La imagen no puede superar los 3 MB.')
        return value
