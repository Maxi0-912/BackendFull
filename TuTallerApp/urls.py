from django.urls import path
from .views import (
    LoginView, GoogleLoginView, RegisterView,
    PerfilView, ActualizarPerfilView, EliminarCuentaView,
    MisVehiculosView, CrearVehiculoView, EliminarVehiculoView,
    ListaEstablecimientosView, DetalleEstablecimientoView,
    ResenasEstablecimientoView, CitasOcupadasView, CrearEstablecimientoView,
    RolesPublicosView, TiposEstablecimientoView, TiposServicioView,
    CrearTipoServicioView, AnunciosPublicosView,
    ServiciosPorEstablecimientoView,
    MisCitasView, CrearCitaView, DetalleCitaView, EditarCitaView, EliminarCitaView,
    CambiarEstadoCitaView, AgregarComentarioEmpresaView,
    CrearCalificacionView, CalificacionesPorEstablecimientoView,
    MisNotificacionesView, MarcarLeidaView,
    DashboardEmpresaView, MisEstablecimientosView, MiEstablecimientoDetailView,
    EmpresaCitasView, EmpresaServiciosView, EmpresaServicioDetailView,
    EmpresaAnunciosView, EmpresaAnuncioDetailView, EmpresaAnuncioCupoView, EmpresaAnuncioPagoView,
    AdminDashboardView,
    AdminUsuarioListView, AdminUsuarioDetailView,
    AdminEstablecimientoDetailView,
    AdminServicioListView, AdminServicioDetailView,
    AdminPrestacionListView, AdminPrestacionDetailView,
    AdminCalificacionListView, AdminCalificacionDetailView,
    AdminNotificacionListView, AdminNotificacionDetailView,
    AdminVehiculoListView, AdminVehiculoDetailView,
    AdminRolListView, AdminRolDetailView,
    AdminTipoEstablecimientoListView, AdminTipoEstablecimientoDetailView,
    AdminTipoServicioListView, AdminTipoServicioDetailView,
    AdminAgendaView,
    AdminAnuncioListView, AdminAnuncioDetailView, AdminAnuncioValidarView,
)

urlpatterns = [
    # Auth
    path('usuarios/register/',          RegisterView.as_view()),
    path('usuarios/login/',             LoginView.as_view()),
    path('usuarios/auth/google/',       GoogleLoginView.as_view()),
    path('usuarios/google-login/',      GoogleLoginView.as_view()),
    path('usuarios/perfil/',            PerfilView.as_view()),
    path('usuarios/perfil/update/',     ActualizarPerfilView.as_view()),
    path('usuarios/perfil/actualizar/', ActualizarPerfilView.as_view()),
    path('usuarios/eliminar-cuenta/',   EliminarCuentaView.as_view()),
    path('auth/eliminar/',              EliminarCuentaView.as_view()),

    # Vehiculos
    path('usuarios/mis-vehiculos/',             MisVehiculosView.as_view()),
    path('usuarios/mis-vehiculos/crear/',       CrearVehiculoView.as_view()),
    path('usuarios/mis-vehiculos/<str:placa>/', EliminarVehiculoView.as_view()),

    # Establecimientos
    path('establecimientos/',                         ListaEstablecimientosView.as_view()),
    path('establecimientos/crear/',                   CrearEstablecimientoView.as_view()),
    path('establecimientos/<int:pk>/',                DetalleEstablecimientoView.as_view()),
    path('establecimientos/<int:pk>/resenas/',        ResenasEstablecimientoView.as_view()),
    path('establecimientos/<int:pk>/citas-ocupadas/', CitasOcupadasView.as_view()),

    # Tipos publicos
    path('roles/',                  RolesPublicosView.as_view()),
    path('tipos-establecimiento/',  TiposEstablecimientoView.as_view()),
    path('tipos-servicio/',         TiposServicioView.as_view()),
    path('tipos-servicio/crear/',   CrearTipoServicioView.as_view()),
    path('anuncios/',               AnunciosPublicosView.as_view()),
    path('api/anuncios/',           AnunciosPublicosView.as_view()),

    # Servicios
    path('servicios/establecimiento/<int:pk>/', ServiciosPorEstablecimientoView.as_view()),

    # Citas
    path('citas/mis-citas/',            MisCitasView.as_view()),
    path('citas/crear/',                CrearCitaView.as_view()),
    path('citas/<int:pk>/',             DetalleCitaView.as_view()),
    path('citas/<int:pk>/editar/',      EditarCitaView.as_view()),
    path('citas/<int:pk>/eliminar/',    EliminarCitaView.as_view()),
    path('citas/<int:pk>/estado/',      CambiarEstadoCitaView.as_view()),
    path('citas/<int:pk>/comentario/',  AgregarComentarioEmpresaView.as_view()),

    # Calificaciones
    path('calificaciones/crear/',                    CrearCalificacionView.as_view()),
    path('calificaciones/establecimiento/<int:pk>/', CalificacionesPorEstablecimientoView.as_view()),

    # Notificaciones
    path('notificaciones/',                MisNotificacionesView.as_view()),
    path('notificaciones/<int:pk>/leida/', MarcarLeidaView.as_view()),

    # Empresa
    path('empresa/dashboard/',                     DashboardEmpresaView.as_view()),
    path('empresa/mis-establecimientos/',           MisEstablecimientosView.as_view()),
    path('empresa/mis-establecimientos/crear/',     MisEstablecimientosView.as_view()),
    path('empresa/mis-establecimientos/<int:pk>/',  MiEstablecimientoDetailView.as_view()),
    path('empresa/citas/',                          EmpresaCitasView.as_view()),
    path('empresa/servicios/',                      EmpresaServiciosView.as_view()),
    path('empresa/servicios/crear/',                EmpresaServiciosView.as_view()),
    path('empresa/servicios/<int:pk>/',             EmpresaServicioDetailView.as_view()),
    path('api/empresa/anuncios/',                   EmpresaAnunciosView.as_view()),
    path('api/empresa/anuncios/cupo/',              EmpresaAnuncioCupoView.as_view()),
    path('api/empresa/anuncios/<int:pk>/',          EmpresaAnuncioDetailView.as_view()),
    path('api/empresa/anuncios/<int:pk>/pago/',     EmpresaAnuncioPagoView.as_view()),

    # Admin
    path('api/admin/dashboard/',                        AdminDashboardView.as_view()),
    path('api/admin/usuarios/',                         AdminUsuarioListView.as_view()),
    path('api/admin/usuarios/<int:pk>/',                AdminUsuarioDetailView.as_view()),
    path('api/admin/establecimientos/<int:pk>/',        AdminEstablecimientoDetailView.as_view()),
    path('api/admin/servicios/',                        AdminServicioListView.as_view()),
    path('api/admin/servicios/<int:pk>/',               AdminServicioDetailView.as_view()),
    path('api/admin/prestaciones/',                     AdminPrestacionListView.as_view()),
    path('api/admin/prestaciones/<int:pk>/',            AdminPrestacionDetailView.as_view()),
    path('api/admin/calificaciones/',                   AdminCalificacionListView.as_view()),
    path('api/admin/calificaciones/<int:pk>/',          AdminCalificacionDetailView.as_view()),
    path('api/admin/notificaciones/',                   AdminNotificacionListView.as_view()),
    path('api/admin/notificaciones/<int:pk>/',          AdminNotificacionDetailView.as_view()),
    path('api/admin/vehiculos/',                        AdminVehiculoListView.as_view()),
    path('api/admin/vehiculos/<str:placa>/',            AdminVehiculoDetailView.as_view()),
    path('api/admin/roles/',                            AdminRolListView.as_view()),
    path('api/admin/roles/<int:pk>/',                   AdminRolDetailView.as_view()),
    path('api/admin/tipos-establecimiento/',            AdminTipoEstablecimientoListView.as_view()),
    path('api/admin/tipos-establecimiento/<int:pk>/',   AdminTipoEstablecimientoDetailView.as_view()),
    path('api/admin/tipos-servicio/',                   AdminTipoServicioListView.as_view()),
    path('api/admin/tipos-servicio/<int:pk>/',          AdminTipoServicioDetailView.as_view()),
    path('api/admin/agenda/',                           AdminAgendaView.as_view()),
    path('api/admin/anuncios/',                         AdminAnuncioListView.as_view()),
    path('api/admin/anuncios/<int:pk>/',                AdminAnuncioDetailView.as_view()),
    path('api/admin/anuncios/<int:pk>/validar/',        AdminAnuncioValidarView.as_view()),
]

