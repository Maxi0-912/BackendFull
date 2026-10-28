"""Pruebas de regresion de los hallazgos del pentest de Tecnoparque (oct-2026).

Cada prueba reproduce el caso del informe y comprueba que ya no es explotable.
"""
import datetime

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Rol, Usuario, Establecimiento, Vehiculo, Cita


class BaseSeguridad(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.rol_admin = Rol.objects.create(pk=1, nombre='Admin')
        cls.rol_cliente = Rol.objects.create(pk=2, nombre='Cliente')
        cls.rol_empresa = Rol.objects.create(pk=3, nombre='Empresa')
        cls.admin = Usuario.objects.create_user('admin_prueba', password='Prueba12345*', rol=cls.rol_admin)
        cls.cliente = Usuario.objects.create_user('cliente_prueba', password='Prueba12345*', rol=cls.rol_cliente)
        cls.empresa = Usuario.objects.create_user('empresa_prueba', password='Prueba12345*', rol=cls.rol_empresa)
        cls.est = Establecimiento.objects.create(nombre='Taller', direccion='Calle 1', propietario=cls.empresa)

    def setUp(self):
        cache.clear()

    def como(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c

    def manana(self):
        return str(datetime.date.today() + datetime.timedelta(days=1))


class RolPerfilTests(BaseSeguridad):
    def test_cliente_no_puede_volverse_empresa(self):
        r = self.como(self.cliente).put('/usuarios/perfil/update/', {'rol': 3}, format='json')
        self.assertEqual(r.status_code, 400)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.rol_id, 2)

    def test_nadie_se_autoasigna_admin(self):
        sin_rol = Usuario.objects.create_user('nuevo', password='x123456')
        r = self.como(sin_rol).patch('/usuarios/perfil/update/', {'rol': 1}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_usuario_sin_rol_puede_elegir_cliente_o_empresa(self):
        sin_rol = Usuario.objects.create_user('google_viejo', password='x123456')
        r = self.como(sin_rol).patch('/usuarios/perfil/update/', {'rol': 3}, format='json')
        self.assertEqual(r.status_code, 200)
        sin_rol.refresh_from_db()
        self.assertEqual(sin_rol.rol_id, 3)

    def test_editar_perfil_normal_sigue_funcionando(self):
        r = self.como(self.cliente).patch('/usuarios/perfil/update/', {'first_name': 'Ana'}, format='json')
        self.assertEqual(r.status_code, 200)


class PanelEmpresaTests(BaseSeguridad):
    RUTAS_GET = ['/empresa/dashboard/', '/empresa/mis-establecimientos/',
                 '/empresa/citas/', '/empresa/servicios/']

    def test_cliente_no_entra_al_panel_empresa(self):
        c = self.como(self.cliente)
        for ruta in self.RUTAS_GET:
            self.assertEqual(c.get(ruta).status_code, 403, ruta)

    def test_cliente_no_crea_establecimientos(self):
        c = self.como(self.cliente)
        for ruta in ['/empresa/mis-establecimientos/crear/', '/establecimientos/crear/']:
            r = c.post(ruta, {'nombre': 'ZZZ_PENTEST', 'direccion': 'x'}, format='json')
            self.assertEqual(r.status_code, 403, ruta)
        self.assertFalse(Establecimiento.objects.filter(nombre='ZZZ_PENTEST').exists())

    def test_empresa_si_entra(self):
        c = self.como(self.empresa)
        for ruta in self.RUTAS_GET:
            self.assertEqual(c.get(ruta).status_code, 200, ruta)
        r = c.post('/empresa/mis-establecimientos/crear/', {'nombre': 'Sede 2', 'direccion': 'x'}, format='json')
        self.assertEqual(r.status_code, 201)


class CitasTests(BaseSeguridad):
    def test_no_reutiliza_vehiculo_de_otro(self):
        Vehiculo.objects.create(placa='ZZZ999', usuario=self.admin)
        r = self.como(self.cliente).post('/citas/crear/', {
            'establecimiento': self.est.pk, 'fecha': self.manana(), 'hora': '10:00', 'placa': 'zzz999',
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertFalse(Cita.objects.exists())

    def test_cita_con_placa_propia_nueva(self):
        r = self.como(self.cliente).post('/citas/crear/', {
            'establecimiento': self.est.pk, 'fecha': self.manana(), 'hora': '10:00', 'placa': 'ABC123',
        }, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Vehiculo.objects.get(placa='ABC123').usuario, self.cliente)

    def test_rechaza_fecha_pasada(self):
        r = self.como(self.cliente).post('/citas/crear/', {
            'establecimiento': self.est.pk, 'fecha': '2020-01-01', 'hora': '10:00',
        }, format='json')
        self.assertEqual(r.status_code, 400)

    def test_establecimiento_inexistente_sin_error_crudo(self):
        r = self.como(self.cliente).post('/citas/crear/', {
            'establecimiento': 99999, 'fecha': self.manana(), 'hora': '10:00',
        }, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertNotIn('foreign key', str(r.data).lower())
        self.assertNotIn('tutalleraunclic', str(r.data).lower())

    def test_cliente_solo_cancela_su_cita(self):
        cita = Cita.objects.create(usuario=self.cliente, establecimiento=self.est,
                                   fecha=self.manana(), hora='10:00')
        c = self.como(self.cliente)
        self.assertEqual(c.patch(f'/citas/{cita.pk}/estado/', {'estado': 'finalizada'}, format='json').status_code, 403)
        self.assertEqual(c.patch(f'/citas/{cita.pk}/estado/', {'estado': 'cancelada'}, format='json').status_code, 200)
        e = self.como(self.empresa)
        self.assertEqual(e.patch(f'/citas/{cita.pk}/estado/', {'estado': 'inventado'}, format='json').status_code, 400)
        self.assertEqual(e.patch(f'/citas/{cita.pk}/estado/', {'estado': 'confirmada'}, format='json').status_code, 200)


class RateLimitTests(BaseSeguridad):
    def test_refresh_bloquea_tras_limite(self):
        c = APIClient()
        codigos = [c.post('/usuarios/login/refresh/', {'refresh': 'basura'}, format='json').status_code
                   for _ in range(25)]
        self.assertIn(429, codigos)

    def test_login_bloquea_tras_limite(self):
        c = APIClient()
        codigos = [c.post('/usuarios/login/', {'username': 'x', 'password': 'y'}, format='json').status_code
                   for _ in range(15)]
        self.assertIn(429, codigos)


class DebugTests(TestCase):
    def test_debug_apagado_por_defecto(self):
        from django.conf import settings
        self.assertFalse(settings.DEBUG)

    def test_404_sin_pagina_tecnica(self):
        r = APIClient().get('/ruta-que-no-existe-xyz-123/')
        self.assertEqual(r.status_code, 404)
        self.assertNotIn(b'URLconf', r.content)
