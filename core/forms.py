from django import forms
from .models import CartaoCredito

class CartaoCreditoForm(forms.ModelForm):
    class Meta:
        model = CartaoCredito
        fields = ['nome', 'limite_total', 'dia_fechamento', 'dia_vencimento']
        # Aplicando as classes do Tailwind diretamente pelo Python
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200'}),
            'limite_total': forms.NumberInput(attrs={'class': 'w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200'}),
            'dia_fechamento': forms.NumberInput(attrs={'class': 'w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200'}),
            'dia_vencimento': forms.NumberInput(attrs={'class': 'w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200'}),
        }