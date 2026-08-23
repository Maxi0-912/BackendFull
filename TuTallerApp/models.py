import os
import secrets

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone


class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    telefono  = models.CharField(max_length=20, blank=True)
    rol       = models.ForeignKey('Rol', on_delete=models.SET_NULL, null=True, blank=True)
    foto      = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    google_id = models.CharField(max_length=150, null=True, blank=True, unique=True)


class TipoEstablecimiento(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


class Establecimiento(models.Model):
    tipo          = models.ForeignKey(TipoEstablecimiento, on_delete=models.SET_NULL, null=True, blank=True)
    nombre        = models.CharField(max_length=150)
    direccion     = models.CharField(max_length=200)
    telefono      = models.CharField(max_length=20, blank=True)
    hora_apertura = models.CharField(max_length=10, blank=True)
    hora_cierre   = models.CharField(max_length=10, blank=True)
    descripcion   = models.TextField(blank=True)
    latitud       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    propietario   = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    foto          = models.ImageField(upload_to='establecimientos/', null=True, blank=True)

    def __str__(self):
        return self.nombre


class FotoEstablecimiento(models.Model):
    establecimiento = models.ForeignKey(
        Establecimiento, on_delete=models.CASCADE, related_name='fotos'
    )
    imagen    = models.ImageField(upload_to='establecimientos/galeria/')
    orden     = models.PositiveIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'creado_en']


class TipoServicio(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    establecimiento = models.ForeignKey(Establecimiento, on_delete=models.CASCADE, related_name='servicios')
    tipo_servicio   = models.ForeignKey(TipoServicio, on_delete=models.CASCADE)
    nombre          = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    TIPO_CHOICES = [
        ('carro',  'Carro'),
        ('moto',   'Moto'),
        ('camion', 'Camion'),
        ('otro',   'Otro'),
    ]
    placa   = models.CharField(max_length=10, primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='vehiculos')
    marca   = models.CharField(max_length=50, blank=True)
    modelo  = models.CharField(max_length=50, blank=True)
    anio    = models.IntegerField(null=True, blank=True)
    tipo    = models.CharField(max_length=20, choices=TIPO_CHOICES, blank=True)

    def __str__(self):
        return self.placa


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada',  'Cancelada'),
        ('finalizada', 'Finalizada'),
    ]
    usuario            = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='citas')
    establecimiento    = models.ForeignKey(Establecimiento, on_delete=models.CASCADE, related_name='citas')
    servicio           = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True, blank=True)
    servicio_texto     = models.CharField(max_length=200, blank=True)
    vehiculo           = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    anuncio_origen     = models.ForeignKey(
        'Anuncio', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='citas_generadas'
    )
    fecha              = models.DateField()
    hora               = models.CharField(max_length=10)
    estado             = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='pendiente')
    descripcion        = models.TextField(blank=True, null=True)
    comentario_empresa = models.TextField(blank=True, null=True)
    creado_en          = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} - {self.establecimiento} - {self.fecha}"


class Calificacion(models.Model):
    cita       = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='calificacion')
    puntuacion = models.IntegerField()
    comentario = models.TextField(blank=True)
    fecha      = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.puntuacion} estrellas"


class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    titulo  = models.CharField(max_length=150)
    mensaje = models.TextField()
    leida   = models.BooleanField(default=False)
    fecha   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.titulo}"


IMAGEN_EXTENSIONES_VALIDAS = ('.jpg', '.jpeg', '.png', '.webp')
IMAGEN_TAMANIO_MAXIMO = 3 * 1024 * 1024  # 3 MB


class Anuncio(models.Model):
    TIPO_CHOICES = [
        ('imagen',       'Solo imagen'),
        ('imagen_texto', 'Imagen con texto'),
        ('imagen_boton', 'Imagen con boton'),
    ]
    CATEGORIA_CHOICES = [
        ('banner', 'Banner'),
        ('oferta', 'Oferta'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado',  'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    CUPO_GRATIS = 3

    titulo          = models.CharField(max_length=200, blank=True)
    descripcion     = models.TextField(blank=True)
    imagen          = models.ImageField(upload_to='anuncios/')
    tipo            = models.CharField(max_length=20, choices=TIPO_CHOICES, default='imagen')
    categoria       = models.CharField(max_length=10, choices=CATEGORIA_CHOICES, default='banner')
    descuento       = models.CharField(max_length=20, blank=True)
    texto_boton     = models.CharField(max_length=50, blank=True)
    url_boton       = models.CharField(max_length=500, blank=True)
    establecimiento = models.ForeignKey(
        'Establecimiento', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='anuncios'
    )
    servicio = models.ForeignKey(
        'Servicio', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='anuncios'
    )
    activo         = models.BooleanField(default=True)
    orden          = models.PositiveIntegerField(default=0)
    fecha_inicio   = models.DateField(null=True, blank=True)
    fecha_fin      = models.DateField(null=True, blank=True)
    estado         = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    motivo_rechazo = models.TextField(blank=True)
    es_pago        = models.BooleanField(default=False)
    pagado         = models.BooleanField(default=False)
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden', '-creado_en']

    def __str__(self):
        return self.titulo or f'Anuncio #{self.id}'

    @property
    def visible_al_publico(self):
        return self.activo and self.estado == 'aprobado' and (not self.es_pago or self.pagado)

    def clean(self):
        super().clean()
        errors = {}

        if self.imagen and self._imagen_cambio():
            extension = os.path.splitext(self.imagen.name or '')[1].lower()
            if extension not in IMAGEN_EXTENSIONES_VALIDAS:
                errors['imagen'] = 'La imagen debe ser JPG, PNG o WEBP.'
            else:
                try:
                    tamanio = self.imagen.size
                except (ValueError, OSError):
                    tamanio = None
                if tamanio and tamanio > IMAGEN_TAMANIO_MAXIMO:
                    errors['imagen'] = 'La imagen no puede superar los 3 MB.'

        if self.url_boton:
            try:
                URLValidator(schemes=['http', 'https'])(self.url_boton)
            except ValidationError:
                errors['url_boton'] = 'La URL debe comenzar con http:// o https://.'

        if self.servicio_id and self.servicio.establecimiento_id != self.establecimiento_id:
            errors['servicio'] = 'El servicio debe pertenecer al mismo establecimiento del anuncio.'

        if errors:
            raise ValidationError(errors)

    def _imagen_cambio(self):
        if not self.pk:
            return True
        imagen_previa = Anuncio.objects.filter(pk=self.pk).values_list('imagen', flat=True).first()
        return imagen_previa != self.imagen.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class PagoPendiente(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente de verificacion'),
        ('verificado', 'Verificado'),
        ('cancelado',  'Cancelado'),
    ]

    anuncio = models.OneToOneField(
        Anuncio, on_delete=models.CASCADE, related_name='pago_pendiente'
    )
    referencia       = models.CharField(max_length=50, unique=True)
    monto            = models.DecimalField(max_digits=10, decimal_places=2, default=15000.00)
    estado           = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    numero_nequi     = models.CharField(max_length=20, default='+57 315 123 4567')
    descripcion      = models.TextField(blank=True)
    creado_en        = models.DateTimeField(auto_now_add=True)
    confirmado_en    = models.DateTimeField(null=True, blank=True)
    admin_usuario    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='pagos_confirmados'
    )

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f'{self.referencia} - {self.get_estado_display()}'

    def _generar_referencia(self):
        prefijo = f"TT{timezone.now().strftime('%Y%m%d')}"
        for _ in range(5):
            candidato = f'{prefijo}{secrets.token_hex(3).upper()}'
            if not PagoPendiente.objects.filter(referencia=candidato).exists():
                return candidato
        return f'{prefijo}{secrets.token_hex(3).upper()}'

    def save(self, *args, **kwargs):
        if not self.referencia:
            self.referencia = self._generar_referencia()

        if self.pk and self.estado == 'verificado':
            estado_previo = PagoPendiente.objects.filter(pk=self.pk).values_list('estado', flat=True).first()
            if estado_previo != 'verificado':
                self.confirmado_en = timezone.now()
                self.anuncio.pagado = True
                self.anuncio.save(update_fields=['pagado', 'actualizado_en'])
        super().save(*args, **kwargs)
