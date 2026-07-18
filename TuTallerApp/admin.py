from django.contrib import admin
from .models import (
    Rol, Usuario, TipoEstablecimiento, Establecimiento,
    TipoServicio, Servicio, Vehiculo,
    Cita, Calificacion, Notificacion, Anuncio,
)


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'fecha_creacion')
    list_filter  = ('activo',)
    search_fields = ('nombre',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display  = ('username', 'email', 'telefono', 'rol')
    list_filter   = ('rol',)
    search_fields = ('username', 'email')


@admin.register(TipoEstablecimiento)
class TipoEstablecimientoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)


@admin.register(Establecimiento)
class EstablecimientoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'tipo', 'telefono', 'propietario')
    list_filter   = ('tipo',)
    search_fields = ('nombre', 'direccion')


@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre',)


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'establecimiento', 'tipo_servicio')
    list_filter  = ('tipo_servicio',)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa', 'usuario', 'marca', 'modelo', 'anio', 'tipo')


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display  = ('id', 'usuario', 'establecimiento', 'fecha', 'hora', 'estado')
    list_filter   = ('estado',)
    search_fields = ('usuario__username', 'establecimiento__nombre')


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('cita', 'puntuacion', 'fecha')


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo', 'leida', 'fecha')
    list_filter  = ('leida',)


@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'establecimiento', 'activo', 'fecha_inicio', 'fecha_fin')
    list_filter  = ('categoria', 'activo')
