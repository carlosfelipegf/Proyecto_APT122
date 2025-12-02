
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from .models import SolicitudInspeccion, Roles, EstadoSolicitud, PlantillaInspeccion

class CotizacionFlowTestCase(TestCase):
	def setUp(self):
		# Crear grupos
		for rol in Roles:
			Group.objects.get_or_create(name=rol.value)
		# Crear usuarios
		self.admin = User.objects.create_user(username='admin', password='admin1234', email='admin@test.com')
		self.admin.groups.add(Group.objects.get(name=Roles.ADMINISTRADOR))
		self.cliente = User.objects.create_user(username='cliente', password='cliente1234', email='cliente@test.com')
		self.cliente.groups.add(Group.objects.get(name=Roles.CLIENTE))
		self.tecnico = User.objects.create_user(username='tecnico', password='tecnico1234', email='tecnico@test.com')
		self.tecnico.groups.add(Group.objects.get(name=Roles.TECNICO))
		# Plantilla
		self.plantilla = PlantillaInspeccion.objects.create(nombre='Base', descripcion='Test')
		# Solicitud
		self.solicitud = SolicitudInspeccion.objects.create(
			cliente=self.cliente,
			nombre_cliente='Cliente',
			direccion='Calle 123',
			telefono='123456789',
			maquinaria='Maquina X',
		)
		self.client = Client()

	def test_flujo_cotizacion(self):
		# Admin cotiza
		self.client.login(username='admin', password='admin1234')
		resp = self.client.post(f'/usuarios/solicitud/gestionar/{self.solicitud.pk}/', {
			'action': 'aprobar',
			'tecnico': self.tecnico.pk,
			'plantilla': self.plantilla.pk,
			'nombre_inspeccion': 'Inspeccion Test',
			'fecha_programada': '',
			'monto_cotizacion': 10000
		})
		self.solicitud.refresh_from_db()
		self.assertEqual(self.solicitud.estado, EstadoSolicitud.COTIZANDO)
		# Cliente acepta
		self.client.logout()
		self.client.login(username='cliente', password='cliente1234')
		resp = self.client.post(f'/usuarios/solicitud/aceptar-cotizacion/{self.solicitud.pk}/', {
			'action': 'aceptar'
		})
		self.solicitud.refresh_from_db()
		self.assertEqual(self.solicitud.estado, EstadoSolicitud.APROBADA)

	def test_flujo_rechazo(self):
		# Admin cotiza
		self.client.login(username='admin', password='admin1234')
		resp = self.client.post(f'/usuarios/solicitud/gestionar/{self.solicitud.pk}/', {
			'action': 'aprobar',
			'tecnico': self.tecnico.pk,
			'plantilla': self.plantilla.pk,
			'nombre_inspeccion': 'Inspeccion Test',
			'fecha_programada': '',
			'monto_cotizacion': 10000
		})
		self.solicitud.refresh_from_db()
		self.assertEqual(self.solicitud.estado, EstadoSolicitud.COTIZANDO)
		# Cliente rechaza
		self.client.logout()
		self.client.login(username='cliente', password='cliente1234')
		resp = self.client.post(f'/usuarios/solicitud/aceptar-cotizacion/{self.solicitud.pk}/', {
			'action': 'rechazar'
		})
		self.solicitud.refresh_from_db()
		self.assertEqual(self.solicitud.estado, EstadoSolicitud.RECHAZADA)
