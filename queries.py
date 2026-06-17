def query_eventos_esocial():
    """
    Retorna a query principal que busca os dados da view vControleEsocial,
    unida à tabela PESOCIALEVENTOS para trazer XML (MENSAGEM), Log de Geração (LOGGERACAO) e Competência.
    """
    return """
        SELECT 
            V.ID,
            V.CODCOLIGADA,
            CONCAT(V.CODCOLIGADA, ' - ', GC.NOMEFANTASIA) AS NOME_COLIGADA,
            V.CHAPA,
            ISNULL(F.NOME, P.NOME) AS NOME_FUNCIONARIO,
            V.TIPOEVENTO,
            V.DATAEVENTO,
            V.MES_EVENTO,
            V.ANO_EVENTO,
            V.STATUS,
            V.FORA_DO_PRAZO,
            V.RECCREATEDBY AS RESPONSAVEL,
            V.RECCREATEDON,
            PE.MENSAGEM,
            PE.LOGGERACAO,
            PE.MESCOMP,
            PE.ANOCOMP
        FROM 
            [dbo].[vControleEsocial] V (NOLOCK)
            INNER JOIN [dbo].[PESOCIALEVENTOS] PE (NOLOCK) ON V.CODCOLIGADA = PE.CODCOLIGADA AND V.ID = PE.ID
            -- JOIN para buscar o nome da Coligada
            LEFT JOIN GCOLIGADA GC (NOLOCK) ON V.CODCOLIGADA = GC.CODCOLIGADA
            -- JOIN para buscar o nome da Pessoa (útil para eventos de admissão inicial)
            LEFT JOIN PPESSOA P (NOLOCK) ON V.CODPESSOA = P.CODIGO
            -- JOIN para buscar o nome do Funcionário na chapa atual
            LEFT JOIN PFUNC F (NOLOCK) ON V.CODCOLIGADA = F.CODCOLIGADA AND V.CHAPA = F.CHAPA
        WHERE 
            V.STATUS NOT IN (10, 11)
            AND V.CODCOLIGADA NOT IN (5, 6)
    """