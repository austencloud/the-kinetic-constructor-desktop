# Browse Tab V2 Defensive Programming Strategy Guide

## Executive Summary

This guide establishes defensive programming patterns for performance-critical code paths in Browse Tab V2. It provides comprehensive error handling, graceful degradation strategies, and resource management protocols to ensure system stability under all conditions.

## Performance-Critical Error Handling Patterns

### 1. Widget Creation Error Handling

**Pattern: Circuit Breaker for Widget Creation**
```python
class WidgetCreationCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def create_widget_safely(self, sequence, index):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
            else:
                return self._create_fallback_widget(sequence, index)
        
        try:
            widget = self._create_widget_with_timeout(sequence, index, timeout=5.0)
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
            return widget
            
        except (WidgetCreationTimeout, MemoryError, RuntimeError) as e:
            self._handle_widget_creation_failure(e, sequence, index)
            return self._create_fallback_widget(sequence, index)
    
    def _handle_widget_creation_failure(self, error, sequence, index):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.critical(f"Widget creation circuit breaker OPEN: {error}")
            self._notify_performance_degradation()
        
        logger.error(f"Widget creation failed for {sequence.id}: {error}")
        self._record_failure_metrics(error, sequence, index)
```

**Pattern: Timeout-Protected Operations**
```python
class TimeoutProtectedOperations:
    @staticmethod
    def with_timeout(operation, timeout_seconds=5.0, fallback=None):
        """Execute operation with timeout protection."""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Operation timed out after {timeout_seconds}s")
        
        # Set timeout signal
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_seconds))
        
        try:
            result = operation()
            signal.alarm(0)  # Cancel timeout
            return result
        except TimeoutError as e:
            logger.warning(f"Operation timeout: {e}")
            return fallback() if fallback else None
        finally:
            signal.signal(signal.SIGALRM, old_handler)
```

### 2. Memory Management Error Handling

**Pattern: Memory Pressure Detection**
```python
class MemoryPressureMonitor:
    def __init__(self, warning_threshold=0.8, critical_threshold=0.9):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.last_gc_time = time.time()
        self.gc_frequency = 30  # seconds
    
    def check_memory_pressure(self):
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent / 100
            
            if memory_percent > self.critical_threshold:
                self._handle_critical_memory_pressure()
                return 'CRITICAL'
            elif memory_percent > self.warning_threshold:
                self._handle_warning_memory_pressure()
                return 'WARNING'
            else:
                return 'NORMAL'
                
        except ImportError:
            # Fallback without psutil
            return self._estimate_memory_pressure()
    
    def _handle_critical_memory_pressure(self):
        logger.critical("Critical memory pressure detected")
        
        # Aggressive cleanup
        self._force_garbage_collection()
        self._clear_non_essential_caches()
        self._reduce_widget_pool_size()
        
        # Notify performance monitor
        self._emit_memory_pressure_signal('CRITICAL')
    
    def _force_garbage_collection(self):
        if time.time() - self.last_gc_time > 5:  # Rate limit GC
            import gc
            collected = gc.collect()
            self.last_gc_time = time.time()
            logger.info(f"Emergency GC collected {collected} objects")
```

### 3. Thread Safety Patterns

**Pattern: Thread-Safe Widget Creation**
```python
class ThreadSafeWidgetManager:
    def __init__(self):
        self._widget_lock = threading.RLock()
        self._creation_queue = queue.Queue()
        self._active_creations = set()
        self._creation_semaphore = threading.Semaphore(4)  # Max 4 concurrent
    
    def create_widget_async(self, sequence, index, callback):
        """Thread-safe asynchronous widget creation."""
        creation_id = f"{sequence.id}_{index}"
        
        with self._widget_lock:
            if creation_id in self._active_creations:
                logger.warning(f"Widget creation already in progress: {creation_id}")
                return False
            
            self._active_creations.add(creation_id)
        
        def creation_worker():
            try:
                with self._creation_semaphore:
                    widget = self._create_widget_thread_safe(sequence, index)
                    
                    # Schedule callback on main thread
                    QTimer.singleShot(0, lambda: self._handle_creation_complete(
                        creation_id, widget, callback
                    ))
                    
            except Exception as e:
                logger.error(f"Widget creation failed in thread: {e}")
                QTimer.singleShot(0, lambda: self._handle_creation_error(
                    creation_id, e, callback
                ))
            finally:
                with self._widget_lock:
                    self._active_creations.discard(creation_id)
        
        threading.Thread(target=creation_worker, daemon=True).start()
        return True
```

## Graceful Degradation Strategies

### 1. Performance Target Degradation

**Strategy: Adaptive Performance Targets**
```python
class AdaptivePerformanceManager:
    def __init__(self):
        self.performance_levels = {
            'HIGH': {'fps': 120, 'batch_size': 32, 'cache_size': 1000},
            'MEDIUM': {'fps': 60, 'batch_size': 16, 'cache_size': 500},
            'LOW': {'fps': 30, 'batch_size': 8, 'cache_size': 200},
            'MINIMAL': {'fps': 15, 'batch_size': 4, 'cache_size': 100}
        }
        self.current_level = 'HIGH'
        self.degradation_history = deque(maxlen=10)
    
    def evaluate_performance_level(self, recent_metrics):
        """Determine appropriate performance level based on system capability."""
        avg_frame_time = sum(recent_metrics.get('frame_times', [])) / max(1, len(recent_metrics.get('frame_times', [])))
        memory_pressure = recent_metrics.get('memory_pressure', 'NORMAL')
        cpu_usage = recent_metrics.get('cpu_usage', 0)
        
        # Degradation logic
        if avg_frame_time > 50 or memory_pressure == 'CRITICAL' or cpu_usage > 90:
            target_level = 'MINIMAL'
        elif avg_frame_time > 33 or memory_pressure == 'WARNING' or cpu_usage > 70:
            target_level = 'LOW'
        elif avg_frame_time > 16.67 or cpu_usage > 50:
            target_level = 'MEDIUM'
        else:
            target_level = 'HIGH'
        
        if target_level != self.current_level:
            self._transition_performance_level(target_level)
    
    def _transition_performance_level(self, new_level):
        old_level = self.current_level
        self.current_level = new_level
        
        logger.info(f"Performance level transition: {old_level} → {new_level}")
        
        # Apply new performance settings
        settings = self.performance_levels[new_level]
        self._apply_performance_settings(settings)
        
        # Record degradation event
        self.degradation_history.append({
            'timestamp': time.time(),
            'from_level': old_level,
            'to_level': new_level,
            'reason': 'automatic_degradation'
        })
```

### 2. Feature Degradation Hierarchy

**Strategy: Progressive Feature Disabling**
```python
class FeatureDegradationManager:
    def __init__(self):
        self.feature_hierarchy = [
            'animations',           # Disable first
            'glassmorphism_effects',
            'predictive_loading',
            'background_processing',
            'image_caching',
            'hover_effects'         # Disable last
        ]
        self.disabled_features = set()
    
    def degrade_features_for_performance(self, performance_level):
        """Progressively disable features based on performance level."""
        features_to_disable = {
            'MINIMAL': self.feature_hierarchy[:4],
            'LOW': self.feature_hierarchy[:3],
            'MEDIUM': self.feature_hierarchy[:2],
            'HIGH': []
        }
        
        target_disabled = set(features_to_disable.get(performance_level, []))
        
        # Disable new features
        for feature in target_disabled - self.disabled_features:
            self._disable_feature(feature)
        
        # Re-enable features if performance improves
        for feature in self.disabled_features - target_disabled:
            self._enable_feature(feature)
        
        self.disabled_features = target_disabled
    
    def _disable_feature(self, feature):
        logger.info(f"Disabling feature for performance: {feature}")
        
        if feature == 'animations':
            self._disable_animations()
        elif feature == 'glassmorphism_effects':
            self._disable_glassmorphism()
        elif feature == 'predictive_loading':
            self._disable_predictive_loading()
        # ... other features
```

## Resource Cleanup Protocols

### 1. Widget Lifecycle Management

**Protocol: Comprehensive Widget Cleanup**
```python
class WidgetLifecycleManager:
    def __init__(self):
        self.active_widgets = weakref.WeakValueDictionary()
        self.cleanup_queue = queue.Queue()
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self._process_cleanup_queue)
        self.cleanup_timer.start(1000)  # Cleanup every second
    
    def register_widget(self, widget_id, widget):
        """Register widget for lifecycle management."""
        self.active_widgets[widget_id] = widget
        
        # Set up automatic cleanup on widget destruction
        widget.destroyed.connect(lambda: self._on_widget_destroyed(widget_id))
    
    def schedule_widget_cleanup(self, widget_id, delay_ms=0):
        """Schedule widget for cleanup."""
        cleanup_time = time.time() + (delay_ms / 1000)
        self.cleanup_queue.put((cleanup_time, widget_id))
    
    def _process_cleanup_queue(self):
        """Process pending widget cleanups."""
        current_time = time.time()
        processed = 0
        
        while not self.cleanup_queue.empty() and processed < 10:  # Rate limit
            try:
                cleanup_time, widget_id = self.cleanup_queue.get_nowait()
                
                if cleanup_time <= current_time:
                    self._cleanup_widget(widget_id)
                    processed += 1
                else:
                    # Put back in queue
                    self.cleanup_queue.put((cleanup_time, widget_id))
                    break
                    
            except queue.Empty:
                break
    
    def _cleanup_widget(self, widget_id):
        """Perform comprehensive widget cleanup."""
        if widget_id in self.active_widgets:
            widget = self.active_widgets[widget_id]
            
            try:
                # Disconnect signals
                self._disconnect_widget_signals(widget)
                
                # Clear references
                self._clear_widget_references(widget)
                
                # Remove from parent
                if widget.parent():
                    widget.setParent(None)
                
                # Schedule for deletion
                widget.deleteLater()
                
                del self.active_widgets[widget_id]
                
            except Exception as e:
                logger.error(f"Widget cleanup failed for {widget_id}: {e}")
```

### 2. Memory Leak Prevention

**Protocol: Proactive Memory Management**
```python
class MemoryLeakPrevention:
    def __init__(self):
        self.reference_tracker = {}
        self.weak_references = weakref.WeakSet()
        self.gc_scheduler = QTimer()
        self.gc_scheduler.timeout.connect(self._scheduled_garbage_collection)
        self.gc_scheduler.start(30000)  # Every 30 seconds
    
    def track_object(self, obj, category='general'):
        """Track object for memory leak detection."""
        obj_id = id(obj)
        self.reference_tracker[obj_id] = {
            'category': category,
            'created_at': time.time(),
            'type': type(obj).__name__
        }
        
        # Use weak reference to avoid keeping object alive
        self.weak_references.add(obj)
    
    def _scheduled_garbage_collection(self):
        """Perform scheduled garbage collection with leak detection."""
        import gc
        
        # Force garbage collection
        collected = gc.collect()
        
        # Check for potential leaks
        self._check_for_memory_leaks()
        
        logger.debug(f"Scheduled GC collected {collected} objects")
    
    def _check_for_memory_leaks(self):
        """Check for potential memory leaks."""
        current_time = time.time()
        leak_threshold = 300  # 5 minutes
        
        potential_leaks = []
        for obj_id, info in list(self.reference_tracker.items()):
            age = current_time - info['created_at']
            
            if age > leak_threshold:
                potential_leaks.append((obj_id, info, age))
        
        if potential_leaks:
            logger.warning(f"Potential memory leaks detected: {len(potential_leaks)} objects")
            for obj_id, info, age in potential_leaks[:5]:  # Log first 5
                logger.warning(f"Long-lived object: {info['type']} ({info['category']}) - {age:.1f}s old")
```

## Production Monitoring and Alerting

### 1. Performance Monitoring System

**System: Real-time Performance Alerts**
```python
class ProductionPerformanceMonitor:
    def __init__(self):
        self.alert_thresholds = {
            'navigation_response_time': 200,  # ms
            'frame_time': 33,                 # ms (30fps minimum)
            'memory_usage': 200,              # MB
            'widget_creation_time': 100       # ms
        }
        self.alert_cooldown = {}
        self.metrics_buffer = defaultdict(deque)
    
    def record_metric(self, metric_name, value):
        """Record performance metric and check for alerts."""
        self.metrics_buffer[metric_name].append({
            'value': value,
            'timestamp': time.time()
        })
        
        # Keep only recent metrics
        cutoff_time = time.time() - 300  # 5 minutes
        while (self.metrics_buffer[metric_name] and 
               self.metrics_buffer[metric_name][0]['timestamp'] < cutoff_time):
            self.metrics_buffer[metric_name].popleft()
        
        # Check for alert conditions
        self._check_alert_conditions(metric_name, value)
    
    def _check_alert_conditions(self, metric_name, current_value):
        """Check if metric exceeds alert thresholds."""
        if metric_name not in self.alert_thresholds:
            return
        
        threshold = self.alert_thresholds[metric_name]
        
        # Check cooldown
        cooldown_key = f"{metric_name}_alert"
        if cooldown_key in self.alert_cooldown:
            if time.time() - self.alert_cooldown[cooldown_key] < 60:  # 1 minute cooldown
                return
        
        if current_value > threshold:
            # Calculate trend
            recent_values = [m['value'] for m in list(self.metrics_buffer[metric_name])[-10:]]
            avg_recent = sum(recent_values) / len(recent_values) if recent_values else current_value
            
            if avg_recent > threshold:
                self._trigger_performance_alert(metric_name, current_value, threshold, avg_recent)
                self.alert_cooldown[cooldown_key] = time.time()
    
    def _trigger_performance_alert(self, metric_name, current_value, threshold, avg_recent):
        """Trigger performance alert."""
        severity = 'CRITICAL' if current_value > threshold * 2 else 'WARNING'
        
        alert_data = {
            'metric': metric_name,
            'current_value': current_value,
            'threshold': threshold,
            'average_recent': avg_recent,
            'severity': severity,
            'timestamp': time.time()
        }
        
        logger.error(f"Performance Alert [{severity}]: {metric_name} = {current_value} > {threshold}")
        
        # Send to monitoring system
        self._send_alert_to_monitoring_system(alert_data)
```

This defensive programming strategy ensures robust performance optimization implementation with comprehensive error handling, graceful degradation, and proactive monitoring to maintain system stability under all conditions.
