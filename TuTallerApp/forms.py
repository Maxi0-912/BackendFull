from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from datetime import date

from .models import (
    Usuario,
    Rol,
    Vehiculo,
    Establecimiento,
    PrestacionServicio,
    Calificacion,
    Agenda
)


# ==============================
# 🔐 REGISTRO USUARIO
# ==============================

class RegistroForm(UserCreationForm):

    rol = forms.ModelChoiceField(
        queryset=Rol.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Seleccione un rol"
    )

    class Meta:
        model = Usuario
        fields = [
            'username',
            'email',
            'telefono',
            'rol',
            'password1',
            'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email


# ==============================
# 🔑 LOGIN
# ==============================

class LoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password'].widget.attrs.update({'class': 'form-control'})


# ==============================
# 🚗 VEHÍCULO
# ==============================

class VehiculoForm(forms.ModelForm):

    class Meta:
        model = Vehiculo
        fields = ['placa']
        widgets = {
            'placa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ABC123'
            })
        }

    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        if Vehiculo.objects.filter(placa=placa).exists():
            raise forms.ValidationError("Esta placa ya está registrada.")
        return placa


# ==============================
# 🏢 ESTABLECIMIENTO
# ==============================

class EstablecimientoForm(forms.ModelForm):

    class Meta:
        model = Establecimiento
        fields = [
            'tipo',
            'nombre',
            'direccion',
            'telefono',
            'hora_apertura',
            'hora_cierre',
            'descripcion',
            'latitud',
            'longitud'
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'hora_apertura': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_cierre': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'latitud': forms.NumberInput(attrs={'step': '0.000001', 'class': 'form-control'}),
            'longitud': forms.NumberInput(attrs={'step': '0.000001', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        apertura = cleaned_data.get('hora_apertura')
        cierre = cleaned_data.get('hora_cierre')

        if apertura and cierre and apertura >= cierre:
            raise forms.ValidationError(
                "La hora de apertura debe ser menor que la hora de cierre."
            )

        return cleaned_data


# ==============================
# 📅 CREAR CITA (PrestacionServicio)
# ==============================

class PrestacionServicioForm(forms.ModelForm):

    class Meta:
        model = PrestacionServicio
        fields = [
            'establecimiento',
            'agenda',
            'vehiculo',
            'servicio',
            'fecha'
        ]
        widgets = {
            'establecimiento': forms.Select(attrs={'class': 'form-control'}),
            'agenda': forms.Select(attrs={'class': 'form-control'}),
            'vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'servicio': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        establecimiento = cleaned_data.get('establecimiento')
        agenda = cleaned_data.get('agenda')
        fecha = cleaned_data.get('fecha')

        if fecha and fecha < date.today():
            raise forms.ValidationError("No puedes agendar en fechas pasadas.")

        if establecimiento and agenda:

            # Validar horario permitido
            if not (establecimiento.hora_apertura <= agenda.hora <= establecimiento.hora_cierre):
                raise forms.ValidationError("Horario fuera del rango permitido.")

            # Evitar doble reserva
            if PrestacionServicio.objects.filter(
                establecimiento=establecimiento,
                agenda=agenda,
                fecha=fecha,
                estado__in=['pendiente', 'confirmada']
            ).exists():
                raise forms.ValidationError("Ese horario ya está reservado.")

        return cleaned_data


# ==============================
# ⭐ CALIFICACIÓN
# ==============================

class CalificacionForm(forms.ModelForm):

    class Meta:
        model = Calificacion
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.RadioSelect(
                choices=[(i, f"{i} ⭐") for i in range(1, 6)]
            ),
            'comentario': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Escribe tu experiencia...'
            })
        }

    def clean_puntuacion(self):
        puntuacion = self.cleaned_data.get('puntuacion')

        if puntuacion < 1 or puntuacion > 5:
            raise forms.ValidationError("La puntuación debe estar entre 1 y 5.")

        return puntuacion