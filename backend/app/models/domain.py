from enum import StrEnum


class DatasetProfile(StrEnum):
    INSCRITOS = "inscritos"
    ADMITIDOS = "admitidos"
    MATRICULADOS = "matriculados"
    MATRICULADOS_PRIMER_CURSO = "matriculados_primer_curso"
    GRADUADOS = "graduados"
    DOCENTES = "docentes"
    METADATOS = "metadatos"


STUDENT_PROFILES = {
    DatasetProfile.INSCRITOS,
    DatasetProfile.ADMITIDOS,
    DatasetProfile.MATRICULADOS,
    DatasetProfile.MATRICULADOS_PRIMER_CURSO,
    DatasetProfile.GRADUADOS,
}

