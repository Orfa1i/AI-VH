# Pinned Synthea FHIR Generator Dockerfile
# Pinned version: Synthea v3.3.0

FROM eclipse-temurin:21-jre-alpine

LABEL maintainer="AI-VH Team"
LABEL synthea.version="v3.3.0"
LABEL description="Deterministic Synthea runner producing valid FHIR R4 transaction bundles"

WORKDIR /app

# Download pinned official release of Synthea
ARG SYNTHEA_VERSION=v3.3.0
ADD https://github.com/synthetichealth/synthea/releases/download/${SYNTHEA_VERSION}/synthea-with-dependencies.jar /app/synthea-with-dependencies.jar

# Add synthea properties configuration enforcing FHIR R4 transaction bundles only
RUN echo "exporter.fhir.export = true" >> /app/synthea.properties && \
    echo "exporter.fhir.transaction_bundle = true" >> /app/synthea.properties && \
    echo "exporter.hospital.fhir.export = false" >> /app/synthea.properties && \
    echo "exporter.practitioner.fhir.export = false" >> /app/synthea.properties && \
    echo "exporter.csv.export = false" >> /app/synthea.properties && \
    echo "exporter.ccda.export = false" >> /app/synthea.properties && \
    echo "exporter.text.export = false" >> /app/synthea.properties

VOLUME ["/output"]

ENTRYPOINT ["java", "-jar", "/app/synthea-with-dependencies.jar", "--config", "/app/synthea.properties", "-d", "/output"]
CMD ["-p", "1"]
