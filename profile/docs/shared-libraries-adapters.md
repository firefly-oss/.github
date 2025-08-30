# Shared Libraries & Adapters Layer - Deep Dive

## Overview

The Shared Libraries & Adapters Layer provides reusable components, utilities, and integration adapters that support all services across the Firefly OpenCore Banking Platform. This layer promotes code reuse, standardizes common functionality, and provides consistent interfaces to external systems.

## Layer Architecture

### Library Characteristics
- **Reusability**: Common functionality shared across multiple services
- **Standardization**: Consistent patterns and implementations
- **Abstraction**: Clean interfaces hiding implementation complexity
- **Extensibility**: Pluggable and configurable components
- **Testing**: Comprehensive unit and integration testing
- **Documentation**: Well-documented APIs and usage patterns

### Module Structure Pattern
```
lib-module-name/
├── lib-module-name-api/        # Public interfaces and contracts
├── lib-module-name-core/       # Core implementation logic
├── lib-module-name-config/     # Configuration and auto-configuration
├── lib-module-name-test/       # Test utilities and fixtures
└── pom.xml                    # Maven configuration and dependencies
```

## Core Common Libraries

### 1. lib-common-core

**Purpose**: Foundational utilities and common patterns used across all platform services.

#### Key Components

##### Base Domain Objects
- **Entity**: Base entity class with ID management
- **ValueObject**: Immutable value object base class
- **AggregateRoot**: Domain aggregate root implementation
- **DomainEvent**: Base domain event structure
- **Result**: Result pattern implementation for error handling

```java path=null start=null
@Data
@NoArgsConstructor
@AllArgsConstructor
public abstract class Entity<T> {
    protected T id;
    protected LocalDateTime createdAt;
    protected LocalDateTime updatedAt;
    protected String createdBy;
    protected String updatedBy;
    protected Long version;
    
    public abstract boolean sameIdentityAs(Entity<T> other);
}

@Data
@EqualsAndHashCode
public abstract class ValueObject {
    // Immutable value object base implementation
}

public class Result<T> {
    private final T data;
    private final String errorMessage;
    private final boolean success;
    
    public static <T> Result<T> success(T data) {
        return new Result<>(data, null, true);
    }
    
    public static <T> Result<T> failure(String errorMessage) {
        return new Result<>(null, errorMessage, false);
    }
}
```

##### Utility Classes
- **DateTimeUtils**: Date and time manipulation utilities
- **StringUtils**: String processing and validation utilities
- **ValidationUtils**: Common validation patterns
- **CryptoUtils**: Cryptographic utilities for hashing and encryption
- **JsonUtils**: JSON serialization/deserialization utilities

##### Exception Handling
- **BusinessException**: Base business logic exception
- **ValidationException**: Data validation exceptions
- **ExternalSystemException**: External system integration exceptions
- **RetryableException**: Exceptions that should trigger retries

#### API Features
- **Pagination**: Standardized pagination support
- **Sorting**: Multi-field sorting capabilities
- **Filtering**: Dynamic filtering framework
- **Response Wrappers**: Consistent API response structures

### 2. lib-common-auth

**Purpose**: Authentication and authorization utilities for secure service communication.

#### Key Components

##### Authentication Support
- **JWT Token Processing**: Token generation, validation, and parsing
- **OAuth2 Integration**: OAuth2 client and resource server support
- **Multi-Factor Authentication**: MFA token generation and validation
- **Session Management**: Secure session handling utilities

```java path=null start=null
@Component
public class JwtTokenProvider {
    
    public String generateToken(Authentication authentication) {
        UserPrincipal userPrincipal = (UserPrincipal) authentication.getPrincipal();
        Date expiryDate = new Date(System.currentTimeMillis() + jwtExpirationInMs);
        
        return Jwts.builder()
                .setSubject(userPrincipal.getId().toString())
                .setIssuedAt(new Date())
                .setExpiration(expiryDate)
                .signWith(SignatureAlgorithm.HS512, jwtSecret)
                .compact();
    }
    
    public boolean validateToken(String authToken) {
        try {
            Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(authToken);
            return true;
        } catch (JwtException | IllegalArgumentException ex) {
            return false;
        }
    }
}
```

##### Authorization Framework
- **Role-Based Access Control**: RBAC implementation
- **Permission Checking**: Fine-grained permission validation
- **Security Context**: Thread-local security context management
- **Audit Logging**: Security event logging and audit trails

##### Security Utilities
- **Password Encryption**: Secure password hashing and validation
- **Data Encryption**: AES encryption for sensitive data
- **Key Management**: Cryptographic key generation and rotation
- **Certificate Handling**: X.509 certificate processing

#### Features
- **Spring Security Integration**: Seamless Spring Security integration
- **Custom Authentication Providers**: Pluggable authentication mechanisms
- **Security Annotations**: Method-level security annotations
- **CORS Configuration**: Cross-origin resource sharing setup

### 3. lib-common-r2dbc

**Purpose**: Reactive database connectivity and ORM utilities for PostgreSQL integration.

#### Key Components

##### R2DBC Configuration
- **Connection Pool Management**: Reactive connection pooling
- **Database Initialization**: Schema and data initialization
- **Transaction Management**: Reactive transaction handling
- **Migration Support**: Database schema migration utilities

```java path=null start=null
@Configuration
@EnableR2dbcRepositories
public class R2dbcConfig extends AbstractR2dbcConfiguration {
    
    @Bean
    public ConnectionFactory connectionFactory() {
        return ConnectionFactories.get(ConnectionFactoryOptions.builder()
                .option(DRIVER, "postgresql")
                .option(HOST, databaseHost)
                .option(PORT, databasePort)
                .option(USER, databaseUser)
                .option(PASSWORD, databasePassword)
                .option(DATABASE, databaseName)
                .build());
    }
    
    @Bean
    public ReactiveTransactionManager transactionManager() {
        return new R2dbcTransactionManager(connectionFactory());
    }
}
```

##### Repository Framework
- **Base Repository**: Generic reactive repository implementation
- **Query Builder**: Dynamic query construction utilities
- **Pagination Support**: Reactive pagination implementation
- **Audit Trail**: Automatic audit field management

##### Data Mapping
- **Entity Mapping**: Object-relational mapping utilities
- **Type Conversion**: Custom data type converters
- **JSON Support**: JSON column mapping and querying
- **Enum Handling**: Database enum type support

#### Features
- **Reactive Streams**: Full reactive programming support
- **Custom Queries**: Native SQL and stored procedure support
- **Database Monitoring**: Connection and query performance monitoring
- **Health Checks**: Database connectivity health checks

### 4. lib-common-kafka

**Purpose**: Apache Kafka integration and event-driven messaging utilities.

#### Key Components

##### Producer Framework
- **Reactive Producer**: Non-blocking message publishing
- **Message Serialization**: JSON and Avro serialization support
- **Partitioning Strategy**: Custom partitioning logic
- **Error Handling**: Producer error handling and retry logic

```java path=null start=null
@Component
public class EventPublisher {
    
    private final ReactiveKafkaTemplate<String, Object> kafkaTemplate;
    
    public Mono<Void> publishEvent(String topic, Object event) {
        return kafkaTemplate.send(topic, event)
                .doOnError(error -> log.error("Failed to publish event", error))
                .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)))
                .then();
    }
    
    public <T> Mono<Void> publishDomainEvent(DomainEvent<T> event) {
        String topic = event.getClass().getSimpleName().toLowerCase();
        return publishEvent(topic, event);
    }
}
```

##### Consumer Framework
- **Reactive Consumer**: Non-blocking message consumption
- **Message Deserialization**: Automatic message deserialization
- **Dead Letter Queue**: Failed message handling
- **Consumer Groups**: Scalable consumer group management

##### Event Sourcing Support
- **Event Store**: Event persistence and retrieval
- **Event Replay**: Event stream replay capabilities
- **Snapshot Support**: Aggregate snapshot management
- **Event Versioning**: Event schema evolution support

#### Features
- **Kafka Streams Integration**: Stream processing capabilities
- **Schema Registry**: Avro schema registry integration
- **Monitoring**: Consumer lag and throughput monitoring
- **Configuration Management**: Environment-specific Kafka configuration

### 5. lib-common-logging

**Purpose**: Centralized logging, monitoring, and observability utilities.

#### Key Components

##### Structured Logging
- **Log Formatting**: JSON structured log formatting
- **Correlation IDs**: Request tracing across services
- **MDC Support**: Mapped Diagnostic Context management
- **Log Filtering**: Log level and content filtering

```java path=null start=null
@Slf4j
@Component
public class StructuredLogger {
    
    public void logBusinessEvent(String eventType, Object eventData) {
        try (MDCCloseable mdcCloseable = MDC.putCloseable("eventType", eventType)) {
            log.info("Business event: {}", JsonUtils.toJson(eventData));
        }
    }
    
    public void logPerformanceMetric(String operation, Duration duration, Map<String, Object> metadata) {
        try (MDCCloseable mdcCloseable = MDC.putCloseable("operation", operation)) {
            MDC.put("duration", duration.toMillis() + "ms");
            log.info("Performance metric: {}", JsonUtils.toJson(metadata));
        }
    }
}
```

##### Metrics Collection
- **Business Metrics**: Domain-specific business metrics
- **Technical Metrics**: System performance and health metrics
- **Custom Metrics**: Application-specific metric collection
- **Metric Aggregation**: Time-based metric aggregation

##### Tracing Support
- **Distributed Tracing**: OpenTelemetry integration
- **Span Management**: Trace span creation and management
- **Trace Context**: Cross-service trace context propagation
- **Sampling Configuration**: Configurable trace sampling

#### Features
- **ELK Integration**: Elasticsearch, Logstash, Kibana integration
- **Prometheus Metrics**: Prometheus metrics exposition
- **Health Indicators**: Application health check indicators
- **Alert Integration**: Alerting system integration

### 6. lib-common-validation

**Purpose**: Comprehensive data validation framework for business rules and data integrity.

#### Key Components

##### Validation Framework
- **Bean Validation**: JSR-303/JSR-349 validation support
- **Custom Validators**: Domain-specific validation rules
- **Async Validation**: Non-blocking validation for external checks
- **Validation Groups**: Conditional validation group support

```java path=null start=null
@Component
public class BusinessRuleValidator {
    
    @Autowired
    private List<BusinessRule> businessRules;
    
    public Mono<ValidationResult> validateEntity(Object entity) {
        return Flux.fromIterable(businessRules)
                .filter(rule -> rule.appliesTo(entity.getClass()))
                .flatMap(rule -> rule.validate(entity))
                .collectList()
                .map(violations -> new ValidationResult(violations));
    }
    
    public interface BusinessRule {
        boolean appliesTo(Class<?> entityType);
        Mono<ValidationViolation> validate(Object entity);
    }
}
```

##### Financial Validation
- **Currency Validation**: Currency code and format validation
- **Amount Validation**: Monetary amount validation and precision
- **Account Number Validation**: Account number format and check digit validation
- **Routing Number Validation**: Bank routing number validation

##### Identity Validation
- **SSN Validation**: Social Security Number validation
- **Tax ID Validation**: Tax identification number validation
- **Email Validation**: Email address format and domain validation
- **Phone Validation**: Phone number format and carrier validation

#### Features
- **Internationalization**: Multi-language validation messages
- **Error Aggregation**: Validation error collection and reporting
- **Conditional Validation**: Context-dependent validation rules
- **Performance Optimization**: Cached and optimized validation

## External System Adapters

### 1. lib-baas-adapter

**Purpose**: Banking-as-a-Service provider integration and abstraction layer.

#### Key Components

##### Provider Abstraction
- **Multi-Provider Support**: Support for multiple BaaS providers
- **Provider Switching**: Runtime provider selection and failover
- **API Normalization**: Consistent interface across different providers
- **Response Mapping**: Provider response standardization

```java path=null start=null
public interface BaasProvider {
    
    Mono<AccountResponse> createAccount(CreateAccountRequest request);
    Mono<TransactionResponse> processTransaction(TransactionRequest request);
    Mono<BalanceResponse> getAccountBalance(String accountId);
    Mono<Void> closeAccount(String accountId);
    
    String getProviderId();
    boolean supports(BaasOperation operation);
}

@Service
public class BaasService {
    
    private final Map<String, BaasProvider> providers;
    
    public Mono<AccountResponse> createAccount(String providerId, CreateAccountRequest request) {
        return Optional.ofNullable(providers.get(providerId))
                .map(provider -> provider.createAccount(request))
                .orElse(Mono.error(new UnsupportedProviderException(providerId)));
    }
}
```

##### Account Management
- **Account Opening**: Multi-provider account creation
- **Account Closure**: Account termination workflows
- **Account Maintenance**: Account update and modification
- **Account Inquiry**: Account information retrieval

##### Transaction Processing
- **Payment Processing**: Multi-rail payment processing
- **Transfer Services**: Account-to-account transfers
- **Transaction History**: Transaction retrieval and reporting
- **Transaction Status**: Real-time transaction status

#### Supported Providers
- **Synapse**: Synapse banking services
- **Unit**: Unit banking platform
- **Treasury Prime**: Treasury Prime banking infrastructure
- **Bond**: Bond financial services platform

### 2. lib-idp-adapter

**Purpose**: Identity Provider integration for authentication and identity management.

#### Key Components

##### Identity Provider Abstraction
- **Multi-IDP Support**: Support for multiple identity providers
- **SSO Integration**: Single sign-on capabilities
- **Federation Support**: Identity federation across providers
- **Profile Synchronization**: User profile data synchronization

```java path=null start=null
public interface IdentityProvider {
    
    Mono<AuthenticationResult> authenticate(String username, String password);
    Mono<UserProfile> getUserProfile(String userId);
    Mono<Void> updateUserProfile(String userId, UserProfile profile);
    Mono<List<String>> getUserRoles(String userId);
    Mono<Void> resetPassword(String userId);
    
    String getProviderId();
    List<AuthenticationMethod> getSupportedMethods();
}

@Service
public class IdentityService {
    
    private final Map<String, IdentityProvider> providers;
    
    public Mono<AuthenticationResult> authenticate(String providerId, String username, String password) {
        return Optional.ofNullable(providers.get(providerId))
                .map(provider -> provider.authenticate(username, password))
                .orElse(Mono.error(new UnsupportedProviderException(providerId)));
    }
}
```

##### Authentication Methods
- **Password Authentication**: Username/password authentication
- **Multi-Factor Authentication**: TOTP, SMS, Email MFA
- **Biometric Authentication**: Fingerprint, face recognition
- **Certificate Authentication**: X.509 certificate authentication

##### User Management
- **User Provisioning**: Automated user account creation
- **Role Management**: Role assignment and revocation
- **Group Management**: User group and organization management
- **Audit Logging**: Identity system audit and compliance

#### Supported Providers
- **Okta**: Okta identity cloud
- **Auth0**: Auth0 identity platform
- **Azure AD**: Microsoft Azure Active Directory
- **AWS Cognito**: Amazon Cognito user pools

### 3. lib-payment-adapter

**Purpose**: Payment network and processor integration abstraction layer.

#### Key Components

##### Payment Network Abstraction
- **Multi-Network Support**: ACH, Wire, RTP, Fedwire support
- **Network Routing**: Intelligent payment routing
- **Status Tracking**: Real-time payment status updates
- **Error Handling**: Payment error handling and recovery

##### Payment Processor Integration
- **Processor Abstraction**: Consistent interface across processors
- **Transaction Processing**: Payment transaction execution
- **Settlement Reporting**: Payment settlement and reconciliation
- **Fee Calculation**: Network and processor fee calculation

#### Supported Networks
- **ACH**: Automated Clearing House
- **Fedwire**: Federal Reserve wire transfer
- **RTP**: Real-Time Payments network
- **SWIFT**: International wire transfers

### 4. lib-credit-bureau-adapter

**Purpose**: Credit bureau integration for credit reporting and monitoring.

#### Key Components

##### Credit Report Retrieval
- **Multi-Bureau Support**: Experian, Equifax, TransUnion integration
- **Report Parsing**: Credit report data extraction and normalization
- **Credit Score Calculation**: FICO and VantageScore calculation
- **Adverse Action**: Adverse action reason code handling

##### Credit Monitoring
- **Credit Alert Processing**: Credit change notifications
- **Identity Monitoring**: Identity theft monitoring
- **Fraud Detection**: Credit fraud detection and alerting
- **Dispute Management**: Credit dispute initiation and tracking

#### Supported Bureaus
- **Experian**: Experian credit services
- **Equifax**: Equifax credit reporting
- **TransUnion**: TransUnion credit services
- **LexisNexis**: LexisNexis risk solutions

## Integration Patterns

### Adapter Pattern Implementation
```mermaid
classDiagram
    class ServiceInterface {
        <<interface>>
        +operation()
    }
    
    class ServiceAdapter {
        -externalService: ExternalService
        +operation()
    }
    
    class ExternalService {
        +externalOperation()
    }
    
    ServiceInterface <|-- ServiceAdapter
    ServiceAdapter --> ExternalService
```

### Circuit Breaker Pattern
```java path=null start=null
@Component
public class ResilientServiceAdapter {
    
    private final CircuitBreaker circuitBreaker;
    private final ExternalService externalService;
    
    public Mono<String> callExternalService(String request) {
        return Mono.fromCallable(() -> circuitBreaker.executeSupplier(() -> 
                externalService.process(request)))
                .subscribeOn(Schedulers.boundedElastic())
                .timeout(Duration.ofSeconds(5))
                .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)));
    }
}
```

### Facade Pattern for Complex Integrations
```java path=null start=null
@Service
public class PaymentFacade {
    
    private final List<PaymentAdapter> paymentAdapters;
    
    public Mono<PaymentResult> processPayment(PaymentRequest request) {
        return selectAdapter(request)
                .flatMap(adapter -> adapter.processPayment(request))
                .onErrorResume(error -> handlePaymentError(request, error));
    }
    
    private Mono<PaymentAdapter> selectAdapter(PaymentRequest request) {
        return Mono.fromCallable(() -> paymentAdapters.stream()
                .filter(adapter -> adapter.supports(request))
                .findFirst()
                .orElseThrow(() -> new UnsupportedPaymentException()));
    }
}
```

## Testing Support

### Test Utilities
- **Mock Services**: Mock implementations for testing
- **Test Data Builders**: Builder pattern for test data creation
- **Integration Test Support**: TestContainers integration
- **Performance Testing**: Load testing utilities

### Test Fixtures
- **Database Fixtures**: Pre-configured test database states
- **Message Fixtures**: Kafka message test fixtures
- **API Response Fixtures**: Mock external API responses
- **Security Test Context**: Test security configurations

## Configuration Management

### Auto-Configuration
- **Spring Boot Auto-Configuration**: Automatic library configuration
- **Conditional Configuration**: Environment-based configuration
- **Property Binding**: Type-safe configuration properties
- **Validation**: Configuration validation on startup

### Environment Support
- **Development**: Local development configuration
- **Testing**: Test environment configuration
- **Staging**: Pre-production configuration
- **Production**: Production-ready configuration

## Performance & Monitoring

### Performance Optimization
- **Connection Pooling**: Database and HTTP connection pooling
- **Caching**: Multi-level caching strategies
- **Batch Processing**: Efficient batch operation support
- **Resource Management**: Proper resource lifecycle management

### Monitoring Integration
- **Health Checks**: Library health check indicators
- **Metrics**: Performance and usage metrics
- **Logging**: Structured logging integration
- **Alerting**: Error and performance alerting

This Shared Libraries & Adapters Layer provides the foundational components and integration capabilities that enable efficient, consistent, and maintainable service development across the entire Firefly OpenCore Banking Platform.
