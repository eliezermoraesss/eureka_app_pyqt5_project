-- QUERY ONDE O PRODUTO É USADO?
  SELECT STRUT.G1_COD AS "Código", PROD.B1_DESC "Descrição" 
                    FROM PROTHEUS12_R27.dbo.SG1010 STRUT 
                    INNER JOIN PROTHEUS12_R27.dbo.SB1010 PROD 
                    ON G1_COD = B1_COD WHERE G1_COMP = 'C-006-041-306' 
                    AND STRUT.G1_REVFIM <> 'ZZZ' AND STRUT.D_E_L_E_T_ <> '*'
                    AND STRUT.G1_REVFIM = (SELECT MAX(G1_REVFIM) 
                                            FROM PROTHEUS12_R27.dbo.SG1010 
                                            WHERE 
                                                G1_COD = 'C-006-041-306' 
                                                AND G1_REVFIM <> 'ZZZ' 
                                                AND STRUT.D_E_L_E_T_ <> '*');
                                               
                                               
                                               
SELECT STRUT.G1_COD AS "Código", PROD.B1_DESC "Descrição" 
                    FROM PROTHEUS12_R27.dbo.SG1010 STRUT 
                    INNER JOIN PROTHEUS12_R27.dbo.SB1010 PROD 
                    ON G1_COD = B1_COD WHERE G1_COMP = 'E6126-005-020' 
                    AND STRUT.G1_REVFIM <> 'ZZZ' AND STRUT.D_E_L_E_T_ <> '*'
                    AND STRUT.G1_REVFIM = (SELECT MAX(G1_REVFIM) 
                                            FROM PROTHEUS12_R27.dbo.SG1010 
                                            WHERE 
                                                G1_COD = 'E6126-005-020' 
                                                AND G1_REVFIM <> 'ZZZ' 
                                                AND STRUT.D_E_L_E_T_ <> '*');

SELECT 
	SC.C1_ZZNUMQP AS "QP",
	SC.C1_NUM AS "SC",
	SC.C1_ITEM AS "Item SC",
	SC.C1_QUANT AS "Qtd. SC",
	SC.C1_PEDIDO AS "Ped. Compra",
	SC.C1_ITEMPED AS "Item Ped.",
	PC.C7_QUANT AS "Qtd. Ped.",
	PC.C7_PRECO AS "Preço Unit. (R$)",
	PC.C7_TOTAL AS "Sub-total (R$)",
	PC.C7_DATPRF AS "Previsão Entrega",
	ITEM_NF.D1_DOC AS "Nota Fiscal Ent.",
	ITEM_NF.D1_QUANT AS "Qtd. Entregue",
	CASE 
	    WHEN ITEM_NF.D1_QUANT IS NULL THEN SC.C1_QUJE 
	    ELSE SC.C1_QUJE - ITEM_NF.D1_QUANT
	END AS "Qtd. Pendente",
	ITEM_NF.D1_DTDIGIT AS "Data Entrega",
	PC.C7_ENCER AS "Status Ped. Compra",
	SC.C1_PRODUTO AS "Código",
	SC.C1_DESCRI AS "Descrição",
	SC.C1_UM AS "UM",
	PROD.B1_ZZLOCAL AS "Endereço:",
	SC.C1_EMISSAO AS "Emissão SC",
	PC.C7_EMISSAO AS "Emissão PC",
	ITEM_NF.D1_EMISSAO AS "Emissão NF",
	SC.C1_ORIGEM AS "Origem",
	SC.C1_OBS AS "Observação",
	SC.C1_LOCAL AS "Cod. Armazém",
	ARM.NNR_DESCRI AS "Desc. Armazém",
	SC.C1_IMPORT AS "Importado?",
	PC.C7_OBS AS "Observações",
	PC.C7_OBSM AS "Observações item",
	FORN.A2_COD AS "Cód. Forn.",
	FORN.A2_NOME AS "Raz. Soc. Forn.",
	FORN.A2_NREDUZ AS "Nom. Fantasia Forn.",
	US.USR_NOME AS "Solicitante",
	PC.S_T_A_M_P_ AS "Aberto em:",
	SC.C1_OP AS "OP"
	FROM 
	    PROTHEUS12_R27.dbo.SC7010 PC
	LEFT JOIN 
	    PROTHEUS12_R27.dbo.SD1010 ITEM_NF
	ON 
	    PC.C7_NUM = ITEM_NF.D1_PEDIDO AND PC.C7_ITEM = ITEM_NF.D1_ITEMPC
	LEFT JOIN
	    PROTHEUS12_R27.dbo.SC1010 SC
	ON 
	    SC.C1_PEDIDO = PC.C7_NUM AND SC.C1_ITEMPED = PC.C7_ITEM
	LEFT JOIN
	    PROTHEUS12_R27.dbo.SA2010 FORN
	ON
	    FORN.A2_COD = PC.C7_FORNECE 
	LEFT JOIN
	    PROTHEUS12_R27.dbo.NNR010 ARM
	ON
	    SC.C1_LOCAL = ARM.NNR_CODIGO
	LEFT JOIN 
	    PROTHEUS12_R27.dbo.SYS_USR US
	ON
	    SC.C1_SOLICIT = US.USR_CODIGO AND US.D_E_L_E_T_ <> '*'
	INNER JOIN 
	    PROTHEUS12_R27.dbo.SB1010 PROD
	ON 
	    PROD.B1_COD = SC.C1_PRODUTO
	WHERE 
	    PC.C7_NUM LIKE '%'
		AND PC.C7_NUMSC LIKE '%'
		AND PC.C7_ZZNUMQP LIKE '%6963'
		AND PC.C7_PRODUTO LIKE '%'
		AND PC.C7_DESC LIKE '%'
		AND PC.C7_DESC LIKE '%%'
		AND SC.C1_OP LIKE '%' 
		AND FORN.A2_NOME LIKE '%'
		AND FORN.A2_NREDUZ LIKE '%%'
		AND SC.C1_LOCAL LIKE '%' 
		AND C1_EMISSAO >= '20180628' AND C1_EMISSAO <= '20240704'
		AND PC.D_E_L_E_T_ <> '*'
		AND SC.D_E_L_E_T_ <> '*'
		AND PROD.D_E_L_E_T_ <> '*'
		
	UNION ALL
	
	SELECT 
		SC.C1_ZZNUMQP AS "QP",
		SC.C1_NUM AS "SC",
		SC.C1_ITEM AS "Item SC",
		SC.C1_QUANT AS "Qtd. SC",
		NULL AS "Ped. Compra",
		NULL AS "Item Ped.",
		NULL AS "Qtd. Ped.",
		NULL AS "Preço Unit. (R$)",
		NULL AS "Sub-total (R$)",
		NULL AS "Previsão Entrega",
		NULL AS "Nota Fiscal Ent.",
		NULL AS "Qtd. Entregue",
		NULL AS "Qtd. Pendente",
		NULL AS "Data Entrega",
		NULL AS "Status Ped. Compra",
		SC.C1_PRODUTO AS "Código",
		SC.C1_DESCRI AS "Descrição",
		SC.C1_UM AS "UM",
		PROD.B1_ZZLOCAL AS "Endereço:",
		SC.C1_EMISSAO AS "Emissão SC",
		NULL AS "Emissão PC",
		NULL AS "Emissão NF",
		SC.C1_ORIGEM AS "Origem",
		SC.C1_OBS AS "Observação",
		SC.C1_LOCAL AS "Cod. Armazém",
		ARM.NNR_DESCRI AS "Desc. Armazém",
		SC.C1_IMPORT AS "Importado?",
		NULL AS "Observações",
		NULL AS "Observações item",
		NULL AS "Cód. Forn.",
		NULL AS "Raz. Soc. Forn.",
		NULL AS "Nom. Fantasia Forn.",
		US.USR_NOME AS "Solicitante",
		NULL AS "Aberto em:",
		SC.C1_OP AS "OP"
		FROM 
		    PROTHEUS12_R27.dbo.SC1010 SC
		LEFT JOIN
		    PROTHEUS12_R27.dbo.NNR010 ARM
		ON 
		    SC.C1_LOCAL = ARM.NNR_CODIGO
		LEFT JOIN 
		    PROTHEUS12_R27.dbo.SYS_USR US
		ON 
		    SC.C1_SOLICIT = US.USR_CODIGO AND US.D_E_L_E_T_ <> '*'
		INNER JOIN 
		    PROTHEUS12_R27.dbo.SB1010 PROD
		ON 
		    PROD.B1_COD = SC.C1_PRODUTO
		WHERE 
		    SC.C1_PEDIDO LIKE '      %'

		AND SC.C1_NUM LIKE '%'
		AND SC.C1_ZZNUMQP LIKE '%6963'
		AND SC.C1_PRODUTO LIKE '%'
		AND SC.C1_DESCRI LIKE '%'
		AND SC.C1_DESCRI LIKE '%%'
		AND SC.C1_OP LIKE '%'
		AND SC.C1_LOCAL LIKE '%'
		AND SC.D_E_L_E_T_ <> '*'
		AND SC.C1_COTACAO <> 'XXXXXX'
		AND C1_EMISSAO >= '20200628' AND C1_EMISSAO <= '20240704'
		AND PROD.D_E_L_E_T_ <> '*'
		ORDER BY "SC" DESC;
