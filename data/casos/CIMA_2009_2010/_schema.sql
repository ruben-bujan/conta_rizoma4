-- ----------------------------------------------------------
-- MDB Tools - A library for reading MS Access database files
-- Copyright (C) 2000-2011 Brian Bruns and others.
-- Files in libmdb are licensed under LGPL and the utilities under
-- the GPL, see COPYING.LIB and COPYING files respectively.
-- Check out http://mdbtools.sourceforge.net
-- ----------------------------------------------------------

-- That file uses encoding UTF-8

CREATE TABLE [00003]
 (
	[IdRegClaN03]			Long Integer, 
	[IdRegClaN02]			Long Integer, 
	[NroOrden03]			Long Integer NOT NULL, 
	[DesClaN03]			Text (80) NOT NULL
);

CREATE TABLE [0001T]
 (
	[IdRegN01]			Long Integer, 
	[IdRegClaN01]			Integer NOT NULL, 
	[N0]			Text (120) NOT NULL
);

CREATE TABLE [0002T]
 (
	[IdRegN02]			Long Integer, 
	[IdRegClaN02]			Integer NOT NULL, 
	[IdRegN01]			Long Integer NOT NULL, 
	[N1]			Text (80) NOT NULL
);

CREATE TABLE [0003T]
 (
	[IdRegN03]			Long Integer, 
	[IdRegClaN03]			Integer NOT NULL, 
	[IdRegN02]			Long Integer NOT NULL, 
	[N2]			Text (80) NOT NULL
);

CREATE TABLE [0005T]
 (
	[IdRegN05]			Long Integer, 
	[IdRegClaN05]			Integer NOT NULL, 
	[IdRegN04]			Long Integer NOT NULL, 
	[N4]			Text (80) NOT NULL
);

CREATE TABLE [0006T]
 (
	[IdRegN06]			Long Integer, 
	[IdRegClaN06]			Integer NOT NULL, 
	[IdRegN05]			Long Integer NOT NULL, 
	[N5]			Text (80) NOT NULL
);

CREATE TABLE [0007T]
 (
	[IdRegN07]			Long Integer, 
	[IdRegClaN07]			Integer NOT NULL, 
	[IdRegN06]			Long Integer NOT NULL, 
	[N6]			Text (80) NOT NULL
);

CREATE TABLE [0008T]
 (
	[IdRegN08]			Long Integer, 
	[IdRegClaN08]			Integer NOT NULL, 
	[IdRegN07]			Long Integer NOT NULL, 
	[N7]			Text (80) NOT NULL
);

CREATE TABLE [03#02_01_TMP_T]
 (
	[Cuenta]			Text (50), 
	[Descripcion]			Text (255), 
	[Debe]			Double, 
	[Haber]			Double, 
	[Saldo]			Double, 
	[SaldoDebe]			Double, 
	[SaldoHaber]			Double, 
	[FechaVencimiento]			DateTime
);

CREATE TABLE [03#02_02_TMP_T]
 (
	[Orden]			Long Integer, 
	[Ejercicio]			Text (50), 
	[Grupo]			Text (100), 
	[Cuenta]			Text (100), 
	[SubCuenta]			Text (100), 
	[PlanGeneralCuentas]			Text (255), 
	[Debe]			Double, 
	[Haber]			Double, 
	[Saldo]			Double
);

CREATE TABLE [0300FaseN1]
 (
	[IdFase1]			Long Integer, 
	[NºO]			Byte, 
	[idDepartamento]			Long Integer NOT NULL, 
	[Nivel1]			Text (30) NOT NULL, 
	[Departamento]			Text (30)
);

CREATE TABLE [0300FaseN2]
 (
	[IdFase2]			Long Integer, 
	[NºO]			Byte, 
	[IdFase1]			Long Integer, 
	[DesFase2]			Text (30) NOT NULL
);

CREATE TABLE [0300FaseN3]
 (
	[IdFase3]			Long Integer, 
	[IdFase2]			Long Integer, 
	[Nº]			Byte, 
	[Nivel 3 Fase]			Text (30) NOT NULL
);

CREATE TABLE [030101T]
 (
	[IDRC]			Long Integer, 
	[Activo?]			Boolean NOT NULL, 
	[Orden]			Long Integer, 
	[Función]			Text (50)
);

CREATE TABLE [030102T]
 (
	[IDRCA]			Long Integer, 
	[Activo?]			Boolean NOT NULL, 
	[IDRC]			Long Integer, 
	[Operación]			Text (50), 
	[Persona]			Text (255), 
	[Acción]			Text (255), 
	[ModoTransac]			Text (20), 
	[PlazoTransacDías]			Long Integer, 
	[Retención%]			Single, 
	[IVA%]			Single, 
	[IRPF%]			Single, 
	[T_Interés]			Single, 
	[P_Interés]			Single, 
	[F_Interíes]			Single, 
	[T_Comisión]			Single, 
	[P_Comisión]			Single, 
	[F_Comisión]			Single, 
	[Cuenta Cobro]			Text (30), 
	[Cuenta Pago]			Text (30)
);

CREATE TABLE [030103T]
 (
	[IDRPA]			Long Integer, 
	[IDRCA]			Long Integer, 
	[Activo?]			Boolean NOT NULL, 
	[Transacción]			Text (50), 
	[Orden]			Long Integer
);

CREATE TABLE [030104T]
 (
	[IDRPAc]			Long Integer, 
	[IDRPA]			Long Integer, 
	[Activo?]			Boolean NOT NULL, 
	[Acción]			Text (50), 
	[¿Emisor¿]			Text (255), 
	[Medio]			Text (255), 
	[¿Receptor¿]			Text (255), 
	[Documento]			Text (255), 
	[Objeto]			Text (255), 
	[Orden]			Long Integer
);

CREATE TABLE [030105T]
 (
	[IDRPAD]			Long Integer, 
	[IDRPAc]			Long Integer, 
	[Fórmula]			Text (50), 
	[Activo?]			Boolean NOT NULL, 
	[CuentaC]			Text (255), 
	[DH]			Text (255), 
	[·Explicación]			Text (255), 
	[Orden]			Long Integer
);

CREATE TABLE [030200T]
 (
	[IDRAD]			Long Integer, 
	[IdMigr]			Double, 
	[NºA]			Double, 
	[NºSA]			Double, 
	[FECHA]			DateTime, 
	[CONCEPTO]			Text (255), 
	[CTA_CORTA]			Text (255), 
	[CLA_PERSONA]			Text (255), 
	[ID_PERSONA]			Text (255), 
	[PERSONA]			Text (255), 
	[D]			Double, 
	[H]			Double
);

CREATE TABLE [0302T]
 (
	[IdRegDiario]			Long Integer, 
	[Idmig]			Long Integer, 
	[IdPerjur]			Long Integer, 
	[NºAsiento]			Long Integer NOT NULL, 
	[fechaVencimiento]			DateTime, 
	[Concepto]			Text (255), 
	[CuentaCorta]			Text (50) NOT NULL, 
	[Persona]			Text (255), 
	[CantidadDebe]			Double NOT NULL, 
	[CantidadHaber]			Double NOT NULL
);

CREATE TABLE [040000]
 (
	[IdRegClaN00]			Long Integer, 
	[IdRegVer]			Long Integer NOT NULL, 
	[DesClaN00]			Text (80)
);

CREATE TABLE [040002]
 (
	[IdRegClaN02]			Long Integer, 
	[IdRegClaN01]			Long Integer, 
	[NroOrden02]			Long Integer NOT NULL, 
	[DesClaN02]			Text (80) NOT NULL
);

CREATE TABLE [040004]
 (
	[IdRegClaN04]			Long Integer, 
	[IdRegClaN03]			Long Integer, 
	[NroOrden04]			Long Integer NOT NULL, 
	[DesClaN04]			Text (80) NOT NULL
);

CREATE TABLE [040005]
 (
	[IdRegClaN05]			Long Integer, 
	[IdRegClaN04]			Long Integer, 
	[NroOrden05]			Long Integer NOT NULL, 
	[DesClaN05]			Text (80) NOT NULL
);

CREATE TABLE [040006]
 (
	[IdRegClaN06]			Long Integer, 
	[IdRegClaN05]			Long Integer, 
	[NroOrden06]			Long Integer NOT NULL, 
	[DesClaN06]			Text (80) NOT NULL
);

CREATE TABLE [040007]
 (
	[IdRegClaN07]			Long Integer, 
	[IdRegClaN06]			Long Integer, 
	[NroOrden07]			Long Integer NOT NULL, 
	[DesClaN07]			Text (80) NOT NULL
);

CREATE TABLE [0401]
 (
	[IdRegPreEle]			Long Integer, 
	[IdRegTipPreEle]			Long Integer NOT NULL, 
	[CódigoPE]			Text (8) NOT NULL, 
	[DescripcionPE]			Text (255) NOT NULL, 
	[UdMedidaPE]			Text (5), 
	[ObservacionesPE]			Text (255), 
	[PrecioPE]			Double, 
	[Ahora]			DateTime NOT NULL, 
	[IdRegVer]			Long Integer
);

CREATE TABLE [0402]
 (
	[IdRegComPre]			Long Integer, 
	[IdRegUniObr]			Long Integer NOT NULL, 
	[IdRegPreEle]			Long Integer NOT NULL, 
	[IdRegOpe]			Long Integer, 
	[MediciónPE]			Single, 
	[RdtoHPreEle]			Single, 
	[RdtoUdPreEle]			Single, 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [0402Base]
 (
	[IdRegBaseComPre]			Long Integer, 
	[IdRegBaseUniObr]			Long Integer NOT NULL, 
	[IdRegBasePreEle]			Long Integer NOT NULL, 
	[IdRegOpe]			Long Integer, 
	[MediciónPE]			Single, 
	[RdtoHPreEle]			Single, 
	[RdtoUdPreEle]			Single, 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [0403]
 (
	[IdRegUniObr]			Long Integer, 
	[NormAux]			Boolean NOT NULL, 
	[DescripciónLarUO]			Memo/Hyperlink (255) NOT NULL, 
	[UdMediciónUO]			Text (6) NOT NULL, 
	[RdtoUO/H]			Long Integer, 
	[CódigoNueUO]			Text (12) NOT NULL, 
	[CódigoSuUO]			Text (12) NOT NULL, 
	[CódigoPaux]			Text (12), 
	[ObservacionesUO]			Memo/Hyperlink (255), 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [0403Base]
 (
	[IdRegBaseUniObr]			Long Integer, 
	[DescripciónLarUO]			Memo/Hyperlink (255) NOT NULL, 
	[UdMediciónUO]			Text (6) NOT NULL, 
	[RdtoUO/H]			Long Integer, 
	[CódigoNueUO]			Text (12) NOT NULL, 
	[CódigoSuUO]			Text (12) NOT NULL, 
	[ObservacionesUO]			Memo/Hyperlink (255), 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [0404]
 (
	[IdRegClaTipMed]			Long Integer, 
	[IdRegTipUdMed]			Long Integer NOT NULL, 
	[DesFigura]			Text (50) NOT NULL, 
	[ConPar1]			Text (24) NOT NULL, 
	[ConPar2]			Text (24), 
	[ConPar3]			Text (24), 
	[ConPar4]			Text (24), 
	[ConPar5]			Text (24), 
	[ConPar6]			Text (24), 
	[ConPar7]			Text (24), 
	[ConPar8]			Text (24), 
	[ConPar9]			Text (24), 
	[Formula]			Text (255), 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [0406]
 (
	[IdRegSinDescompuesto]			Long Integer, 
	[IdRegUniObr]			Long Integer, 
	[Precio]			Double
);

CREATE TABLE [0406Base]
 (
	[IdRegBaseSinDescompuesto]			Long Integer, 
	[IdRegBaseUniObr]			Long Integer, 
	[Precio]			Double
);

CREATE TABLE [0407]
 (
	[IdUOporCap]			Long Integer, 
	[IdRegClaN07]			Long Integer NOT NULL, 
	[IdRegUniObr]			Long Integer NOT NULL
);

CREATE TABLE [9001]
 (
	[IdRegForTran]			Long Integer, 
	[DesForRec]			Text (50) NOT NULL
);

CREATE TABLE [9002]
 (
	[DesFormato]			Text (50) NOT NULL, 
	[IdRegForFis]			Long Integer
);

CREATE TABLE [9003]
 (
	[IdRegForLeg]			Long Integer, 
	[DesForRec]			Text (50) NOT NULL
);

CREATE TABLE [9005]
 (
	[IdRegTipDoc]			Long Integer, 
	[Tipodocumento]			Text (50) NOT NULL
);

CREATE TABLE [9007]
 (
	[IdFormaPago]			Long Integer, 
	[FormaPago]			Text (50)
);

CREATE TABLE [9008]
 (
	[IdRegTipAsiento]			Long Integer, 
	[DesAsientoDiario]			Text (24) NOT NULL
);

CREATE TABLE [9009]
 (
	[IdRegTipoReg]			Long Integer, 
	[DesTipoRegistro]			Text (24) NOT NULL
);

CREATE TABLE [9011]
 (
	[IdRegConceptoSinPrecio]			Long Integer, 
	[DesConceptoSinPrecio]			Text (50) NOT NULL
);

CREATE TABLE [9012]
 (
	[IdRegTranPer]			Long Integer, 
	[TipoTran]			Text (50)
);

CREATE TABLE [9014]
 (
	[IdRegTipUdMed]			Long Integer, 
	[TipMedN1]			Text (12) NOT NULL, 
	[TipMedN2]			Text (8) NOT NULL, 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [9015]
 (
	[IdRegOpe]			Long Integer, 
	[DescripcionLarOpe]			Text (50) NOT NULL, 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [9916]
 (
	[IdRegTipPreEle]			Long Integer, 
	[CódigoTPE]			Text (12), 
	[DescripciónTPE]			Text (24) NOT NULL, 
	[NroOrden]			Long Integer NOT NULL, 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [A1DomPersonaFísica]
 (
	[IDDomPerFis]			Long Integer, 
	[Localidad]			Text (100) NOT NULL, 
	[IdFilPerFis]			Long Integer NOT NULL, 
	[CPDomPerFis]			Text (6), 
	[CalleNº]			Text (60), 
	[Tlf]			Text (15), 
	[Fax]			Text (15), 
	[Internet]			Text (40), 
	[Activo/Inactivo]			Boolean NOT NULL
);

CREATE TABLE [AA0Grupo]
 (
	[IDGrupo]			Long Integer, 
	[IdFilPerJur]			Unknown_0012, 
	[Composición]			Text (255)
);

CREATE TABLE [AA1Central]
 (
	[IDCentral]			Long Integer, 
	[IdGrupo]			Long Integer, 
	[IdDomDeEmp]			Long Integer NOT NULL, 
	[Central]			Text (50) NOT NULL
);

CREATE TABLE [AA1sCargoCentral]
 (
	[IDCargoCentral]			Long Integer, 
	[IdCentral]			Long Integer, 
	[IdTrabajoCentral]			Long Integer, 
	[IdPueTra]			Long Integer
);

CREATE TABLE [AA1sTrabajoCentral]
 (
	[IDTrabajoCentral]			Long Integer, 
	[NºO]			Byte NOT NULL, 
	[TrabajoCentral]			Text (50) NOT NULL
);

CREATE TABLE [AA2Departamento]
 (
	[IDDepartamento]			Long Integer, 
	[NºO]			Long Integer, 
	[IdCentral]			Long Integer NOT NULL, 
	[Departamento]			Text (50) NOT NULL
);

CREATE TABLE [AA4Área]
 (
	[IDÁrea]			Long Integer, 
	[IDDivisión]			Long Integer NOT NULL, 
	[Área]			Text (50) NOT NULL
);

CREATE TABLE [AB0PuestoTrabajo]
 (
	[IDPueTra]			Long Integer, 
	[IdDomPerJur]			Long Integer NOT NULL, 
	[IdFilPerFis]			Long Integer NOT NULL, 
	[Cargo]			Text (70), 
	[TlfDirecto]			Text (15), 
	[FaxParticular]			Text (15), 
	[TlfMovivl]			Text (15), 
	[Activo/Inactivo]			Boolean NOT NULL
);

CREATE TABLE [AB1Delegación]
 (
	[IDDelegación]			Long Integer, 
	[IDDepartamento]			Long Integer NOT NULL, 
	[IDDomPerJur]			Long Integer NOT NULL, 
	[Delegación]			Text (50) NOT NULL
);

CREATE TABLE [AB1sTCargoDelegación]
 (
	[IdCargoDelegación]			Long Integer, 
	[IdDelegación]			Long Integer, 
	[IdPueTra]			Long Integer
);

CREATE TABLE [AB2GrupoObra]
 (
	[IDGrupObra]			Long Integer, 
	[IDDelegación]			Long Integer NOT NULL, 
	[GrupObra]			Text (50) NOT NULL
);

CREATE TABLE [AB50Obra-Fase]
 (
	[IdObraFase]			Long Integer, 
	[IdObra]			Long Integer NOT NULL, 
	[Fase]			Text (20) NOT NULL
);

CREATE TABLE [B0PersonaJurídica]
 (
	[IDFilPerJur]			Long Integer, 
	[IdTPersona]			Unknown_0012, 
	[NombreCorto]			Text (50) NOT NULL, 
	[NombreLargo]			Text (255) NOT NULL, 
	[CIFDeEmp]			Text (9) NOT NULL, 
	[Logo]			OLE (255), 
	[LogoPath]			Text (50), 
	[Activo/Inactivo]			Boolean NOT NULL
);

CREATE TABLE [B1DomPersonaJurídica]
 (
	[IDDomPerJur]			Long Integer, 
	[IdFilPerJur]			Long Integer NOT NULL, 
	[ClaveClaLoc]			Text (50), 
	[CP]			Text (6), 
	[TipoDirección]			Text (24), 
	[Dirección]			Text (60), 
	[TlfCentralita]			Text (15), 
	[TlfMovil]			Text (15), 
	[Fax]			Text (15), 
	[Internet]			Text (40), 
	[Web]			Memo/Hyperlink (255), 
	[Activo/Inactivo]			Boolean NOT NULL
);

CREATE TABLE [CA0Obra-Organización]
 (
	[IdObraOrganización]			Long Integer, 
	[IdObra]			Long Integer, 
	[IdÁrea]			Long Integer, 
	[IdGrupObra]			Long Integer
);

CREATE TABLE [DiarioCima]
 (
	[Id]			Long Integer, 
	[Id Mig]			Double, 
	[IdPerJur]			Double, 
	[NA]			Double, 
	[FV]			DateTime, 
	[Concepto]			Text (255), 
	[Cuenta corta]			Text (255), 
	[Persona]			Text (255), 
	[CantidadDebe]			Double NOT NULL, 
	[CantidadHaber]			Double NOT NULL
);

CREATE TABLE [E0TipoProyecto]
 (
	[IdTipProy]			Long Integer, 
	[NºOrdTipProy]			Long Integer, 
	[DesTipProy]			Text (255)
);

CREATE TABLE [E1Proyecto]
 (
	[IdPro]			Long Integer, 
	[IdTipProy]			Long Integer, 
	[IdObra]			Long Integer NOT NULL, 
	[CostesIndirectos]			Single, 
	[GastosGenerales]			Single, 
	[BeneficioIndustrial]			Single, 
	[IVA]			Single, 
	[Pers1Titulo]			Text (100), 
	[Pers1Nombre]			Text (50), 
	[Pers2Titulo]			Text (100), 
	[Pers2Nombre]			Text (50), 
	[Pers3Titulo]			Text (100), 
	[Pers3Nombre]			Text (50), 
	[Pers4Titulo]			Text (100), 
	[Pers4Nombre]			Text (50), 
	[Activo/Inactivo]			Boolean NOT NULL, 
	[Oferta]			Unknown_0012, 
	[PCAP]			Unknown_0012, 
	[Proyecto]			Unknown_0012
);

CREATE TABLE [E2ProyectoVersión]
 (
	[IdTipVerProy]			Long Integer, 
	[VersiónParaFase]			Text (20), 
	[ÁmbitoDeEstudio]			Text (20), 
	[AfectaA]			Unknown_0012, 
	[Descripción]			Text (255), 
	[Activo/Inactivo]			Boolean NOT NULL
);

CREATE TABLE [EDProyecto-Versión]
 (
	[IdVer]			Long Integer, 
	[IdTipVerProy]			Long Integer, 
	[IdPro]			Long Integer NOT NULL, 
	[DesCorVer]			Text (50) NOT NULL, 
	[DesLarVer]			Memo/Hyperlink (255) NOT NULL, 
	[FechaProyecto]			DateTime, 
	[Activo/Inactivo]			Boolean NOT NULL
);

CREATE TABLE [F00Persona]
 (
	[IDTPersona]			Long Integer, 
	[TPersona]			Text (50)
);

CREATE TABLE [F01SubTipoPersona]
 (
	[IDSTPersona]			Long Integer, 
	[IdTPersona]			Long Integer, 
	[TContrato]			Text (50)
);

CREATE TABLE [F02TContrato]
 (
	[IDTContrato]			Long Integer, 
	[IdSTPersona]			Long Integer, 
	[STContrato]			Text (50)
);

CREATE TABLE [F03TRecurso]
 (
	[IDTRecurso]			Long Integer, 
	[IdTContrato]			Long Integer, 
	[TRecurso]			Text (50)
);

CREATE TABLE [F04TObjeto]
 (
	[IDToNJETO]			Long Integer, 
	[IdTRecurso]			Long Integer, 
	[TObjeto]			Text (50)
);

CREATE TABLE [MDAT]
 (
	[Id]			Long Integer, 
	[cUENTA]			Text (255), 
	[NºAsient]			Long Integer, 
	[Fecha]			DateTime, 
	[Concepto]			Text (255), 
	[Persona]			Text (255), 
	[Debe]			Single, 
	[Haber]			Single, 
	[Saldo]			Single
);

CREATE TABLE [0004T]
 (
	[IdRegN04]			Long Integer, 
	[IdRegClaN04]			Integer NOT NULL, 
	[IdRegN03]			Long Integer NOT NULL, 
	[N3]			Text (80) NOT NULL
);

CREATE TABLE [0301T]
 (
	[IdRegAsientoDiario]			Long Integer, 
	[NºAsiento]			Long Integer, 
	[FechaAsientoDiario]			DateTime NOT NULL, 
	[Concepto]			Text (80), 
	[DocsRef]			Unknown_0012
);

CREATE TABLE [040001]
 (
	[IdRegClaN01]			Long Integer, 
	[IdRegClaN00]			Long Integer, 
	[NroOrden01]			Long Integer NOT NULL, 
	[DesClaN01]			Text (80) NOT NULL
);

CREATE TABLE [0401Base]
 (
	[IdRegBasePreEle]			Long Integer, 
	[IdRegTipPreEle]			Long Integer NOT NULL, 
	[CódigoPE]			Text (8) NOT NULL, 
	[DescripcionPE]			Text (255) NOT NULL, 
	[UdMedidaPE]			Text (5), 
	[PrecioPE]			Double, 
	[ObservacionesPE]			Text (255), 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [0405]
 (
	[IdRegMed]			Long Integer, 
	[IdRegUniObr]			Long Integer NOT NULL, 
	[IdRegClaTipMed]			Long Integer, 
	[DesMed]			Text (255), 
	[ValorParámetro1]			Double NOT NULL, 
	[ValorParámetro2]			Double, 
	[ValorParámetro3]			Double, 
	[ValorParámetro4]			Double, 
	[ValorParámetro5]			Double, 
	[ValorParámetro6]			Double, 
	[ValorParámetro7]			Double, 
	[ValorParámetro8]			Double, 
	[ValorParámetro9]			Double, 
	[Ahora]			DateTime NOT NULL
);

CREATE TABLE [9004]
 (
	[IdRegForProc]			Long Integer, 
	[DesForRec]			Text (50) NOT NULL
);

CREATE TABLE [9010]
 (
	[IdRegConcepto]			Long Integer, 
	[DesConcepto]			Text (50) NOT NULL, 
	[PrecioConcepto]			Double, 
	[Unidad]			Text (50)
);

CREATE TABLE [A0PersonaFísica]
 (
	[IDFilPerFis]			Long Integer, 
	[Nombre]			Text (26), 
	[Apellidos]			Text (26), 
	[TlfMovil]			Text (15), 
	[NIF]			Text (12), 
	[Activo/Inactivo]			Boolean NOT NULL
);

CREATE TABLE [AA3División]
 (
	[IDDivisión]			Long Integer, 
	[IDDepartamento]			Long Integer NOT NULL, 
	[División]			Text (255)
);

CREATE TABLE [ABArea-Fase]
 (
	[IdÁreaObra]			Long Integer, 
	[IdÁrea]			Long Integer NOT NULL, 
	[IdObra]			Long Integer, 
	[Procedimiento]			Text (20) NOT NULL
);

CREATE TABLE [D0Obra]
 (
	[IdObra]			Long Integer, 
	[IDDivisión]			Long Integer, 
	[IDGrupObra]			Long Integer, 
	[TipObra]			Text (255), 
	[SubObra]			Unknown_0012, 
	[NomCorObra]			Text (44), 
	[Nombrelargo]			Memo/Hyperlink (255), 
	[SuClaveObra]			Text (24), 
	[SuExpdteObra]			Text (24)
);

CREATE TABLE [Errores de pegado]
 (
	[IdRegDiario]			Memo/Hyperlink (255), 
	[fechaVencimiento]			Memo/Hyperlink (255), 
	[Concepto]			Memo/Hyperlink (255), 
	[CuentaCorta]			Memo/Hyperlink (255), 
	[Persona]			Memo/Hyperlink (255), 
	[CantidadDebe]			Memo/Hyperlink (255), 
	[CantidadHaber]			Memo/Hyperlink (255)
);


