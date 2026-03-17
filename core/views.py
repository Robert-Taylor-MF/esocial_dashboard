from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime
from .models import Categoria
from .models import CartaoCredito, Transacao, Pessoa
from .services import processar_fatura_pdf
from .forms import CartaoCreditoForm

def dashboard(request):
    ultimas_transacoes = Transacao.objects.all().order_by('-data_compra')[:15]
    categorias = Categoria.objects.all()
    
    # 1. Pega o dono do sistema (Você)
    dono = Pessoa.objects.filter(is_owner=True).first()
    renda = dono.renda_mensal if dono else 0
    
    # 2. Calcula as fatias ideais (O Plano de Jogo)
    meta_essencial = float(renda) * 0.50
    meta_emocao = float(renda) * 0.30
    meta_futuro = float(renda) * 0.20
    
    # 3. Pega só os SEUS gastos (ignora o que os amigos devem)
    meus_gastos = Transacao.objects.filter(responsavel=dono)
    
    # 4. Soma o que você já gastou em cada tipo de categoria
    # Usamos float() para garantir que a divisão na tela não dê erro de tipo
    gasto_essencial = float(meus_gastos.filter(categoria__tipo_regra='ESSENCIAL').aggregate(Sum('valor'))['valor__sum'] or 0)
    gasto_emocao = float(meus_gastos.filter(categoria__tipo_regra='ESTILO_VIDA').aggregate(Sum('valor'))['valor__sum'] or 0)
    gasto_futuro = float(meus_gastos.filter(categoria__tipo_regra='FUTURO').aggregate(Sum('valor'))['valor__sum'] or 0)

    # 5. Calcula a porcentagem consumida para a barra de progresso (proteção contra divisão por zero)
    pct_essencial = min(int((gasto_essencial / meta_essencial) * 100) if meta_essencial > 0 else 0, 100)
    pct_emocao = min(int((gasto_emocao / meta_emocao) * 100) if meta_emocao > 0 else 0, 100)
    pct_futuro = min(int((gasto_futuro / meta_futuro) * 100) if meta_futuro > 0 else 0, 100)

    contexto = {
        'transacoes': ultimas_transacoes,
        'categorias': categorias,
        'renda': renda,
        'gastos': {
            'essencial': gasto_essencial, 'emocao': gasto_emocao, 'futuro': gasto_futuro
        },
        'metas': {
            'essencial': meta_essencial, 'emocao': meta_emocao, 'futuro': meta_futuro
        },
        'pcts': {
            'essencial': pct_essencial, 'emocao': pct_emocao, 'futuro': pct_futuro
        }
    }
    
    return render(request, 'dashboard.html', contexto)

def importar_fatura(request):
    # Busca os cartões no banco para montar o "Select" (dropdown) na tela
    cartoes = CartaoCredito.objects.all()
    
    if request.method == 'POST':
        # Recebe o arquivo PDF e o ID do cartão selecionado
        arquivo_pdf = request.FILES.get('fatura_pdf')
        cartao_id = request.POST.get('cartao_id')
        mes_fatura = request.POST.get('mes_fatura')
        ano_fatura = request.POST.get('ano_fatura')
        
        if arquivo_pdf and cartao_id and mes_fatura and ano_fatura:
            sucesso, mensagem = processar_fatura_pdf(arquivo_pdf, cartao_id, mes_fatura, ano_fatura)
            if sucesso:
                # O Django tem um sistema nativo de alertas (messages) para a tela
                messages.success(request, mensagem)
            else:
                messages.error(request, mensagem)
        else:
            messages.warning(request, "Por favor, selecione um cartão e envie um PDF.")
            
    return render(request, 'importar_fatura.html', {'cartoes': cartoes})

def gerenciar_cartoes(request):
    cartoes = CartaoCredito.objects.all()
    
    if request.method == 'POST':
        form = CartaoCreditoForm(request.POST)
        if form.is_valid():
            form.save() # Salva direto no banco!
            messages.success(request, "Cartão forjado com sucesso!")
            return redirect('gerenciar_cartoes') # Recarrega a página limpa
    else:
        form = CartaoCreditoForm()
        
    return render(request, 'gerenciar_cartoes.html', {'form': form, 'cartoes': cartoes})

def ratear_transacao(request, transacao_id):
    # Puxa a transação original do banco
    transacao_original = get_object_or_404(Transacao, id=transacao_id)
    # Puxa todas as pessoas cadastradas para você escolher com quem dividir
    pessoas = Pessoa.objects.filter(ativo=True)
    
    if request.method == 'POST':
        # Vamos somar para garantir que você não dividiu errado (ex: dividiu 140 sendo que a conta era 130)
        soma_rateio = Decimal('0.00')
        novos_registros = []
        
        for pessoa in pessoas:
            # Pega o valor digitado para essa pessoa no formulário (se houver)
            valor_str = request.POST.get(f'valor_pessoa_{pessoa.id}')
            
            if valor_str and float(valor_str) > 0:
                valor_decimal = Decimal(valor_str.replace(',', '.'))
                soma_rateio += valor_decimal
                
                # Prepara a nova transação
                descricao_rateio = f"{transacao_original.descricao} (Rateio: {pessoa.nome})"
                
                novos_registros.append(
                    Transacao(
                        descricao=descricao_rateio,
                        valor=valor_decimal,
                        data_compra=transacao_original.data_compra,
                        responsavel=pessoa,
                        cartao=transacao_original.cartao,
                        categoria=transacao_original.categoria,
                        status=transacao_original.status
                    )
                )
        
        # Regra de Ouro Financeira: O rateio TEM que bater com o valor original
        if soma_rateio != transacao_original.valor:
            messages.error(request, f"A soma da divisão (R$ {soma_rateio}) não bate com o valor original (R$ {transacao_original.valor}).")
        else:
            # Salva as novas transações no banco
            Transacao.objects.bulk_create(novos_registros)
            # Deleta a transação original para não duplicar sua fatura
            transacao_original.delete()
            
            messages.success(request, "Despesa fragmentada com sucesso!")
            return redirect('dashboard') # Volta para a tela inicial
            
    return render(request, 'ratear_transacao.html', {
        'transacao': transacao_original,
        'pessoas': pessoas
    })
    
def extrato_faturas(request):
    transacoes = Transacao.objects.all().order_by('-data_compra')
    cartoes = CartaoCredito.objects.all()
    categorias = Categoria.objects.all()

    # Captura os filtros que vierem pela URL (método GET)
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    cartao_id = request.GET.get('cartao_id')

    # Aplica os filtros no QuerySet se eles existirem
    if mes:
        transacoes = transacoes.filter(mes_fatura=mes)
    if ano:
        transacoes = transacoes.filter(ano_fatura=ano)
    if cartao_id:
        transacoes = transacoes.filter(cartao_id=cartao_id)

    # Valores padrão para os campos do filtro não ficarem vazios
    contexto = {
        'transacoes': transacoes,
        'cartoes': cartoes,
        'categorias': categorias,
        'mes_atual': mes or str(datetime.now().month),
        'ano_atual': ano or str(datetime.now().year),
        'cartao_selecionado': cartao_id or ""
    }
    return render(request, 'extrato.html', contexto)