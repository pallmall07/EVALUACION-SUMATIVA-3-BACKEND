from django import forms

from .models import Category, Product


class CategoryForm(forms.ModelForm):
	class Meta:
		model = Category
		fields = ('name', 'description', 'active')


class ProductForm(forms.ModelForm):
	code = forms.RegexField(
		regex=r'^CAF-[0-9]{3}$',
		label='Código',
		error_messages={
			'invalid': 'Usa el formato CAF-000, por ejemplo CAF-123.',
		},
	)
	price = forms.IntegerField(
		label='Precio (CLP)',
		min_value=100,
		max_value=20000,
		error_messages={
			'min_value': 'El precio mínimo es $100.',
			'max_value': 'El precio máximo es $20.000.',
			'invalid': 'Ingresa un precio entero válido.',
		},
	)
	stock = forms.IntegerField(
		label='Stock',
		min_value=0,
		error_messages={
			'min_value': 'El stock no puede ser negativo.',
			'invalid': 'Ingresa una cantidad entera válida.',
		},
	)

	class Meta:
		model = Product
		fields = ('code', 'name', 'price', 'stock', 'available', 'category')


class OrderForm(forms.Form):
	"""Formulario para los datos de contacto y entrega de un pedido."""

	ORDER_TYPE_CHOICES = (
		("pickup", "Recoger en tienda"),
		("delivery", "Entrega a domicilio"),
	)

	customer_name = forms.CharField(label="Nombre", max_length=100)
	phone = forms.CharField(label="Teléfono", max_length=20)
	email = forms.EmailField(label="Correo electrónico", required=False)
	order_type = forms.ChoiceField(label="Tipo de pedido", choices=ORDER_TYPE_CHOICES)
	address = forms.CharField(
		label="Dirección de entrega",
		max_length=250,
		required=False,
	)
	notes = forms.CharField(label="Notas del pedido", required=False, widget=forms.Textarea)

	def clean(self):
		cleaned_data = super().clean()
		if (
			cleaned_data.get("order_type") == "delivery"
			and not cleaned_data.get("address", "").strip()
		):
			self.add_error("address", "Indica la dirección para la entrega.")
		return cleaned_data
