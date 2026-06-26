// Autor: Jeshua Romero Guadarrama
// Tarea 2: CI/CD para un ETL de Ventas con Python
// Curso: CI/CD para Workflows de Datos con Python
//
// Pipeline as code del ETL de ventas. La idea es que cada cambio en el
// repositorio pase siempre por las mismas etapas, de forma reproducible:
//
//   Build -> Preparar datos -> Test -> Run -> (post: reporte y artefactos)
//
// Uso Docker como agente para que el entorno sea identico en cualquier nodo de
// Jenkins: no dependo de que Python o pandas esten instalados en la maquina.

pipeline {

    // Construimos una imagen a partir del Dockerfile del repo y corremos todas
    // las etapas dentro de ese contenedor.
    agent {
        dockerfile {
            filename 'Dockerfile'
        }
    }

    options {
        // No nos quedamos colgados si algo se traba
        timeout(time: 15, unit: 'MINUTES')
        // Conservamos un historial acotado de ejecuciones
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Build') {
            // Build: dejamos en el log la version exacta del entorno. La imagen
            // ya se construyo con el Dockerfile (agente), aqui la verificamos.
            steps {
                sh 'python --version'
                sh 'pip freeze'
                // Carpeta donde pytest dejara el reporte JUnit
                sh 'mkdir -p reports'
            }
        }

        stage('Preparar datos') {
            // Preparamos los datos ANTES de ejecutar: validamos que el dataset
            // crudo exista para no fallar mas adelante por un archivo ausente.
            steps {
                sh 'test -f data/ventas.csv'
                sh 'echo "Dataset de entrada disponible: data/ventas.csv"'
            }
        }

        stage('Test') {
            // Las pruebas unitarias son la red de seguridad del ETL. Generamos
            // el reporte en formato JUnit para que Jenkins lo muestre.
            steps {
                sh 'pytest -v --junitxml=reports/junit.xml'
            }
        }

        stage('Run') {
            // Ejecutamos el ETL completo sobre el dataset crudo y dejamos los
            // resultados en 'output/'.
            steps {
                sh '''python run_pipeline.py \
                    --input data/ventas.csv \
                    --output output/ventas_limpias.csv'''
            }
        }
    }

    post {
        always {
            // Publicamos el reporte de pruebas y archivamos todo lo generado
            junit 'reports/junit.xml'
            archiveArtifacts artifacts: 'output/**', fingerprint: true, allowEmptyArchive: true
        }
        success {
            echo 'Pipeline del ETL de ventas finalizado correctamente.'
        }
        failure {
            echo "El pipeline fallo. Revisar: ${env.BUILD_URL}console"
        }
    }
}
