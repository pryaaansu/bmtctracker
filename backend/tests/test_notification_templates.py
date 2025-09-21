"""
Tests for notification templates system
"""
import pytest
from app.services.notification_templates import (
    NotificationTemplate,
    NotificationTemplateManager,
    TemplateType,
    Language
)

class TestNotificationTemplate:
    """Test notification template functionality"""
    
    @pytest.fixture
    def sample_template(self):
        """Create sample notification template"""
        return NotificationTemplate(
            template_type=TemplateType.BUS_ARRIVAL,
            language=Language.ENGLISH,
            sms_template="Bus {vehicle_number} arriving at {stop_name} in {eta_minutes} min",
            voice_template="Bus {vehicle_number} is arriving at {stop_name} in {eta_minutes} minutes",
            whatsapp_template="*Bus Alert*\nBus: {vehicle_number}\nStop: {stop_name}\nETA: {eta_minutes} min",
            push_template="Bus {vehicle_number} - {eta_minutes} min",
            variables=["vehicle_number", "stop_name", "eta_minutes"]
        )
    
    def test_render_sms_template(self, sample_template):
        """Test rendering SMS template"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'stop_name': 'Majestic',
            'eta_minutes': '5'
        }
        
        result = sample_template.render('sms', variables)
        
        assert result == "Bus KA01AB1234 arriving at Majestic in 5 min"
    
    def test_render_voice_template(self, sample_template):
        """Test rendering voice template"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'stop_name': 'Majestic',
            'eta_minutes': '5'
        }
        
        result = sample_template.render('voice', variables)
        
        assert result == "Bus KA01AB1234 is arriving at Majestic in 5 minutes"
    
    def test_render_whatsapp_template(self, sample_template):
        """Test rendering WhatsApp template"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'stop_name': 'Majestic',
            'eta_minutes': '5'
        }
        
        result = sample_template.render('whatsapp', variables)
        
        expected = "*Bus Alert*\nBus: KA01AB1234\nStop: Majestic\nETA: 5 min"
        assert result == expected
    
    def test_render_with_missing_variables(self, sample_template):
        """Test rendering with missing variables"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            # Missing stop_name and eta_minutes
        }
        
        result = sample_template.render('sms', variables)
        
        # Should still work but with empty placeholders removed
        assert 'KA01AB1234' in result
        assert '{stop_name}' not in result  # Placeholders should be removed
        assert '{eta_minutes}' not in result
    
    def test_render_unknown_channel(self, sample_template):
        """Test rendering with unknown channel"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'stop_name': 'Majestic',
            'eta_minutes': '5'
        }
        
        # Should fallback to SMS template
        result = sample_template.render('unknown_channel', variables)
        
        assert result == "Bus KA01AB1234 arriving at Majestic in 5 min"

class TestNotificationTemplateManager:
    """Test notification template manager"""
    
    @pytest.fixture
    def template_manager(self):
        """Create template manager for testing"""
        return NotificationTemplateManager()
    
    def test_get_template_english(self, template_manager):
        """Test getting English template"""
        template = template_manager.get_template(TemplateType.BUS_ARRIVAL, Language.ENGLISH)
        
        assert template is not None
        assert template.language == Language.ENGLISH
        assert template.template_type == TemplateType.BUS_ARRIVAL
    
    def test_get_template_kannada(self, template_manager):
        """Test getting Kannada template"""
        template = template_manager.get_template(TemplateType.BUS_ARRIVAL, Language.KANNADA)
        
        assert template is not None
        assert template.language == Language.KANNADA
        assert template.template_type == TemplateType.BUS_ARRIVAL
    
    def test_get_template_fallback_to_english(self, template_manager):
        """Test fallback to English when requested language not available"""
        # Register only English template for a custom type
        custom_template = NotificationTemplate(
            template_type=TemplateType.BUS_DELAY,
            language=Language.ENGLISH,
            sms_template="Test template",
            voice_template="Test template",
            whatsapp_template="Test template",
            push_template="Test template",
            variables=[]
        )
        
        template_manager.register_template(custom_template)
        
        # Try to get Kannada version (should fallback to English)
        template = template_manager.get_template(TemplateType.BUS_DELAY, Language.KANNADA)
        
        assert template is not None
        assert template.language == Language.ENGLISH
    
    def test_get_nonexistent_template(self, template_manager):
        """Test getting non-existent template"""
        # Create a custom template type that doesn't exist
        from enum import Enum
        
        class CustomTemplateType(str, Enum):
            CUSTOM = "custom"
        
        template = template_manager.get_template(CustomTemplateType.CUSTOM, Language.ENGLISH)
        
        assert template is None
    
    def test_render_notification_bus_arrival(self, template_manager):
        """Test rendering bus arrival notification"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'route_number': '500D',
            'stop_name': 'Majestic',
            'eta_minutes': 3
        }
        
        message = template_manager.render_notification(
            TemplateType.BUS_ARRIVAL, 'sms', variables, Language.ENGLISH
        )
        
        assert 'KA01AB1234' in message
        assert '500D' in message
        assert 'Majestic' in message
        assert '3 min' in message
    
    def test_render_notification_bus_arrival_urgent(self, template_manager):
        """Test rendering urgent bus arrival notification"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'route_number': '500D',
            'stop_name': 'Majestic',
            'eta_minutes': 1  # Urgent - 1 minute
        }
        
        message = template_manager.render_notification(
            TemplateType.BUS_ARRIVAL, 'sms', variables, Language.ENGLISH
        )
        
        # Should contain urgency indicator
        assert 'Hurry' in message or '🏃‍♂️' in message
    
    def test_render_notification_bus_arrival_kannada(self, template_manager):
        """Test rendering bus arrival notification in Kannada"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'route_number': '500D',
            'stop_name_kn': 'ಮೆಜೆಸ್ಟಿಕ್',
            'eta_minutes': 3
        }
        
        message = template_manager.render_notification(
            TemplateType.BUS_ARRIVAL, 'sms', variables, Language.KANNADA
        )
        
        assert 'KA01AB1234' in message
        assert '500D' in message
        assert 'ಮೆಜೆಸ್ಟಿಕ್' in message
        assert '3' in message
        assert 'ನಿಮಿಷದಲ್ಲಿ' in message  # "in minutes" in Kannada
    
    def test_render_notification_bus_delay(self, template_manager):
        """Test rendering bus delay notification"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'route_number': '500D',
            'stop_name': 'Majestic',
            'eta_minutes': 10
        }
        
        message = template_manager.render_notification(
            TemplateType.BUS_DELAY, 'sms', variables, Language.ENGLISH
        )
        
        assert 'delayed' in message.lower()
        assert 'KA01AB1234' in message
        assert '10 min' in message
    
    def test_render_notification_emergency_alert(self, template_manager):
        """Test rendering emergency alert notification"""
        variables = {
            'alert_message': 'Service disruption on Route 500D due to traffic'
        }
        
        message = template_manager.render_notification(
            TemplateType.EMERGENCY_ALERT, 'sms', variables, Language.ENGLISH
        )
        
        assert '🚨' in message
        assert 'EMERGENCY ALERT' in message
        assert 'Service disruption' in message
        assert 'Stay safe' in message
    
    def test_render_notification_subscription_confirmed(self, template_manager):
        """Test rendering subscription confirmed notification"""
        variables = {
            'stop_name': 'Majestic',
            'channel': 'SMS',
            'eta_threshold': 5
        }
        
        message = template_manager.render_notification(
            TemplateType.SUBSCRIPTION_CONFIRMED, 'sms', variables, Language.ENGLISH
        )
        
        assert '✅' in message
        assert 'confirmed' in message.lower()
        assert 'Majestic' in message
        assert 'SMS' in message
        assert '5 min' in message
    
    def test_render_notification_whatsapp_formatting(self, template_manager):
        """Test WhatsApp-specific formatting"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'route_number': '500D',
            'stop_name': 'Majestic',
            'eta_minutes': 3
        }
        
        message = template_manager.render_notification(
            TemplateType.BUS_ARRIVAL, 'whatsapp', variables, Language.ENGLISH
        )
        
        # Should contain WhatsApp markdown formatting
        assert '*Bus Alert*' in message
        assert '*KA01AB1234*' in message
        assert '*500D*' in message
        assert '*Majestic*' in message
    
    def test_render_notification_nonexistent_template(self, template_manager):
        """Test rendering with non-existent template"""
        from enum import Enum
        
        class CustomTemplateType(str, Enum):
            CUSTOM = "custom"
        
        variables = {'message': 'Test message'}
        
        message = template_manager.render_notification(
            CustomTemplateType.CUSTOM, 'sms', variables, Language.ENGLISH
        )
        
        # Should return fallback message
        assert 'Notification:' in message
        assert 'Test message' in message
    
    def test_get_available_templates(self, template_manager):
        """Test getting available templates"""
        available = template_manager.get_available_templates()
        
        assert isinstance(available, dict)
        assert TemplateType.BUS_ARRIVAL.value in available
        assert TemplateType.BUS_DELAY.value in available
        assert TemplateType.EMERGENCY_ALERT.value in available
        
        # Each template type should have language variants
        for template_type, languages in available.items():
            assert isinstance(languages, list)
            assert Language.ENGLISH.value in languages
    
    def test_validate_template_variables_valid(self, template_manager):
        """Test template variable validation with valid variables"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            'route_number': '500D',
            'stop_name': 'Majestic',
            'eta_minutes': 3,
            'urgency_suffix': '',
            'urgency_message': ''
        }
        
        missing = template_manager.validate_template_variables(
            TemplateType.BUS_ARRIVAL, variables, Language.ENGLISH
        )
        
        assert len(missing) == 0
    
    def test_validate_template_variables_missing(self, template_manager):
        """Test template variable validation with missing variables"""
        variables = {
            'vehicle_number': 'KA01AB1234',
            # Missing other required variables
        }
        
        missing = template_manager.validate_template_variables(
            TemplateType.BUS_ARRIVAL, variables, Language.ENGLISH
        )
        
        assert len(missing) > 0
        assert 'route_number' in missing
        assert 'stop_name' in missing
        assert 'eta_minutes' in missing
    
    def test_validate_template_variables_nonexistent_template(self, template_manager):
        """Test template variable validation with non-existent template"""
        from enum import Enum
        
        class CustomTemplateType(str, Enum):
            CUSTOM = "custom"
        
        variables = {}
        
        missing = template_manager.validate_template_variables(
            CustomTemplateType.CUSTOM, variables, Language.ENGLISH
        )
        
        assert len(missing) == 1
        assert 'Template not found' in missing[0]
    
    def test_register_custom_template(self, template_manager):
        """Test registering custom template"""
        custom_template = NotificationTemplate(
            template_type=TemplateType.BUS_CANCELLED,
            language=Language.ENGLISH,
            sms_template="Bus {vehicle_number} on route {route_number} has been cancelled",
            voice_template="Bus {vehicle_number} on route {route_number} has been cancelled",
            whatsapp_template="*Bus Cancelled*\nBus: {vehicle_number}\nRoute: {route_number}",
            push_template="Bus {vehicle_number} cancelled",
            variables=["vehicle_number", "route_number"]
        )
        
        template_manager.register_template(custom_template)
        
        # Should be able to retrieve the custom template
        retrieved = template_manager.get_template(TemplateType.BUS_CANCELLED, Language.ENGLISH)
        
        assert retrieved is not None
        assert retrieved.template_type == TemplateType.BUS_CANCELLED
        assert retrieved.language == Language.ENGLISH