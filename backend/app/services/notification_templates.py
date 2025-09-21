"""
Notification template system with multilingual support
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)

class TemplateType(str, Enum):
    """Types of notification templates"""
    BUS_ARRIVAL = "bus_arrival"
    BUS_DELAY = "bus_delay"
    BUS_CANCELLED = "bus_cancelled"
    ROUTE_DISRUPTION = "route_disruption"
    EMERGENCY_ALERT = "emergency_alert"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    WELCOME = "welcome"

class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    KANNADA = "kn"

@dataclass
class NotificationTemplate:
    """Notification template with multilingual support"""
    template_type: TemplateType
    language: Language
    sms_template: str
    voice_template: str
    whatsapp_template: str
    push_template: str
    variables: List[str]
    
    def render(self, channel: str, variables: Dict[str, Any]) -> str:
        """Render template with variables for specific channel"""
        template_map = {
            'sms': self.sms_template,
            'voice': self.voice_template,
            'whatsapp': self.whatsapp_template,
            'push': self.push_template
        }
        
        template = template_map.get(channel, self.sms_template)
        return self._substitute_variables(template, variables)
    
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template"""
        try:
            # Use safe substitution to avoid KeyError for missing variables
            for var_name, var_value in variables.items():
                placeholder = f"{{{var_name}}}"
                template = template.replace(placeholder, str(var_value))
            
            # Remove any remaining placeholders
            template = re.sub(r'\{[^}]+\}', '', template)
            
            return template.strip()
            
        except Exception as e:
            logger.error(f"Failed to substitute variables in template: {str(e)}")
            return template

class NotificationTemplateManager:
    """Manages notification templates"""
    
    def __init__(self):
        self.templates: Dict[str, Dict[str, NotificationTemplate]] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default templates"""
        
        # Bus Arrival Templates - English
        self.register_template(NotificationTemplate(
            template_type=TemplateType.BUS_ARRIVAL,
            language=Language.ENGLISH,
            sms_template="🚌 Bus {vehicle_number} (Route {route_number}) arriving at {stop_name} in {eta_minutes} min{urgency_suffix}",
            voice_template="Bus {vehicle_number} on route {route_number} is arriving at {stop_name} in {eta_minutes} minutes",
            whatsapp_template="🚌 *Bus Alert*\n\nBus: *{vehicle_number}*\nRoute: *{route_number}*\nStop: *{stop_name}*\nETA: *{eta_minutes} minutes*{urgency_message}",
            push_template="Bus {vehicle_number} arriving in {eta_minutes} min",
            variables=["vehicle_number", "route_number", "stop_name", "eta_minutes", "urgency_suffix", "urgency_message"]
        ))
        
        # Bus Arrival Templates - Kannada
        self.register_template(NotificationTemplate(
            template_type=TemplateType.BUS_ARRIVAL,
            language=Language.KANNADA,
            sms_template="🚌 ಬಸ್ {vehicle_number} (ಮಾರ್ಗ {route_number}) {stop_name_kn} ನಲ್ಲಿ {eta_minutes} ನಿಮಿಷದಲ್ಲಿ ಬರುತ್ತಿದೆ{urgency_suffix}",
            voice_template="ಮಾರ್ಗ {route_number} ರ ಬಸ್ {vehicle_number} {stop_name_kn} ನಲ್ಲಿ {eta_minutes} ನಿಮಿಷದಲ್ಲಿ ಬರುತ್ತಿದೆ",
            whatsapp_template="🚌 *ಬಸ್ ಎಚ್ಚರಿಕೆ*\n\nಬಸ್: *{vehicle_number}*\nಮಾರ್ಗ: *{route_number}*\nನಿಲ್ದಾಣ: *{stop_name_kn}*\nETA: *{eta_minutes} ನಿಮಿಷಗಳು*{urgency_message}",
            push_template="ಬಸ್ {vehicle_number} {eta_minutes} ನಿಮಿಷದಲ್ಲಿ ಬರುತ್ತಿದೆ",
            variables=["vehicle_number", "route_number", "stop_name_kn", "eta_minutes", "urgency_suffix", "urgency_message"]
        ))
        
        # Bus Delay Templates - English
        self.register_template(NotificationTemplate(
            template_type=TemplateType.BUS_DELAY,
            language=Language.ENGLISH,
            sms_template="⏰ Bus {vehicle_number} (Route {route_number}) is delayed. New ETA: {eta_minutes} min at {stop_name}",
            voice_template="Bus {vehicle_number} on route {route_number} is delayed. New estimated arrival time is {eta_minutes} minutes at {stop_name}",
            whatsapp_template="⏰ *Bus Delayed*\n\nBus: *{vehicle_number}*\nRoute: *{route_number}*\nStop: *{stop_name}*\nNew ETA: *{eta_minutes} minutes*\n\nSorry for the inconvenience!",
            push_template="Bus {vehicle_number} delayed - ETA {eta_minutes} min",
            variables=["vehicle_number", "route_number", "stop_name", "eta_minutes"]
        ))
        
        # Bus Delay Templates - Kannada
        self.register_template(NotificationTemplate(
            template_type=TemplateType.BUS_DELAY,
            language=Language.KANNADA,
            sms_template="⏰ ಬಸ್ {vehicle_number} (ಮಾರ್ಗ {route_number}) ತಡವಾಗಿದೆ. ಹೊಸ ETA: {stop_name_kn} ನಲ್ಲಿ {eta_minutes} ನಿಮಿಷ",
            voice_template="ಮಾರ್ಗ {route_number} ರ ಬಸ್ {vehicle_number} ತಡವಾಗಿದೆ. ಹೊಸ ಅಂದಾಜು ಆಗಮನ ಸಮಯ {stop_name_kn} ನಲ್ಲಿ {eta_minutes} ನಿಮಿಷಗಳು",
            whatsapp_template="⏰ *ಬಸ್ ತಡವಾಗಿದೆ*\n\nಬಸ್: *{vehicle_number}*\nಮಾರ್ಗ: *{route_number}*\nನಿಲ್ದಾಣ: *{stop_name_kn}*\nಹೊಸ ETA: *{eta_minutes} ನಿಮಿಷಗಳು*\n\nಅನಾನುಕೂಲತೆಗಾಗಿ ಕ್ಷಮಿಸಿ!",
            push_template="ಬಸ್ {vehicle_number} ತಡವಾಗಿದೆ - ETA {eta_minutes} ನಿಮಿಷ",
            variables=["vehicle_number", "route_number", "stop_name_kn", "eta_minutes"]
        ))
        
        # Emergency Alert Templates - English
        self.register_template(NotificationTemplate(
            template_type=TemplateType.EMERGENCY_ALERT,
            language=Language.ENGLISH,
            sms_template="🚨 EMERGENCY ALERT: {alert_message}. Please follow safety instructions. Stay safe!",
            voice_template="Emergency alert. {alert_message}. Please follow safety instructions and stay safe.",
            whatsapp_template="🚨 *EMERGENCY ALERT*\n\n{alert_message}\n\nPlease follow safety instructions and stay safe!\n\n*BMTC Emergency Services*",
            push_template="🚨 Emergency: {alert_message}",
            variables=["alert_message"]
        ))
        
        # Emergency Alert Templates - Kannada
        self.register_template(NotificationTemplate(
            template_type=TemplateType.EMERGENCY_ALERT,
            language=Language.KANNADA,
            sms_template="🚨 ತುರ್ತು ಎಚ್ಚರಿಕೆ: {alert_message}. ದಯವಿಟ್ಟು ಸುರಕ್ಷತಾ ಸೂಚನೆಗಳನ್ನು ಅನುಸರಿಸಿ. ಸುರಕ್ಷಿತವಾಗಿರಿ!",
            voice_template="ತುರ್ತು ಎಚ್ಚರಿಕೆ. {alert_message}. ದಯವಿಟ್ಟು ಸುರಕ್ಷತಾ ಸೂಚನೆಗಳನ್ನು ಅನುಸರಿಸಿ ಮತ್ತು ಸುರಕ್ಷಿತವಾಗಿರಿ.",
            whatsapp_template="🚨 *ತುರ್ತು ಎಚ್ಚರಿಕೆ*\n\n{alert_message}\n\nದಯವಿಟ್ಟು ಸುರಕ್ಷತಾ ಸೂಚನೆಗಳನ್ನು ಅನುಸರಿಸಿ ಮತ್ತು ಸುರಕ್ಷಿತವಾಗಿರಿ!\n\n*BMTC ತುರ್ತು ಸೇವೆಗಳು*",
            push_template="🚨 ತುರ್ತು: {alert_message}",
            variables=["alert_message"]
        ))
        
        # Subscription Confirmed Templates - English
        self.register_template(NotificationTemplate(
            template_type=TemplateType.SUBSCRIPTION_CONFIRMED,
            language=Language.ENGLISH,
            sms_template="✅ Subscription confirmed for {stop_name} via {channel}. You'll get alerts {eta_threshold} min before bus arrival.",
            voice_template="Your subscription for {stop_name} has been confirmed. You will receive alerts {eta_threshold} minutes before bus arrival.",
            whatsapp_template="✅ *Subscription Confirmed*\n\nStop: *{stop_name}*\nChannel: *{channel}*\nAlert Time: *{eta_threshold} minutes before arrival*\n\nThank you for using BMTC Tracker!",
            push_template="✅ Subscription confirmed for {stop_name}",
            variables=["stop_name", "channel", "eta_threshold"]
        ))
        
        # Subscription Confirmed Templates - Kannada
        self.register_template(NotificationTemplate(
            template_type=TemplateType.SUBSCRIPTION_CONFIRMED,
            language=Language.KANNADA,
            sms_template="✅ {stop_name_kn} ಗಾಗಿ {channel} ಮೂಲಕ ಚಂದಾದಾರಿಕೆ ದೃಢೀಕರಿಸಲಾಗಿದೆ. ಬಸ್ ಆಗಮನಕ್ಕೆ {eta_threshold} ನಿಮಿಷ ಮೊದಲು ಎಚ್ಚರಿಕೆ ಸಿಗುತ್ತದೆ.",
            voice_template="{stop_name_kn} ಗಾಗಿ ನಿಮ್ಮ ಚಂದಾದಾರಿಕೆ ದೃಢೀಕರಿಸಲಾಗಿದೆ. ಬಸ್ ಆಗಮನಕ್ಕೆ {eta_threshold} ನಿಮಿಷಗಳ ಮೊದಲು ಎಚ್ಚರಿಕೆ ಸಿಗುತ್ತದೆ.",
            whatsapp_template="✅ *ಚಂದಾದಾರಿಕೆ ದೃಢೀಕರಿಸಲಾಗಿದೆ*\n\nನಿಲ್ದಾಣ: *{stop_name_kn}*\nಚಾನೆಲ್: *{channel}*\nಎಚ್ಚರಿಕೆ ಸಮಯ: *ಆಗಮನಕ್ಕೆ {eta_threshold} ನಿಮಿಷಗಳ ಮೊದಲು*\n\nBMTC ಟ್ರ್ಯಾಕರ್ ಬಳಸಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು!",
            push_template="✅ {stop_name_kn} ಗಾಗಿ ಚಂದಾದಾರಿಕೆ ದೃಢೀಕರಿಸಲಾಗಿದೆ",
            variables=["stop_name_kn", "channel", "eta_threshold"]
        ))
    
    def register_template(self, template: NotificationTemplate):
        """Register a notification template"""
        template_key = f"{template.template_type.value}_{template.language.value}"
        
        if template.template_type.value not in self.templates:
            self.templates[template.template_type.value] = {}
        
        self.templates[template.template_type.value][template.language.value] = template
        
        logger.info(f"Registered template: {template_key}")
    
    def get_template(self, template_type: TemplateType, 
                    language: Language = Language.ENGLISH) -> Optional[NotificationTemplate]:
        """Get a notification template"""
        templates_for_type = self.templates.get(template_type.value, {})
        
        # Try to get template for requested language
        template = templates_for_type.get(language.value)
        
        # Fallback to English if requested language not available
        if not template and language != Language.ENGLISH:
            template = templates_for_type.get(Language.ENGLISH.value)
        
        return template
    
    def render_notification(self, template_type: TemplateType, channel: str,
                          variables: Dict[str, Any], 
                          language: Language = Language.ENGLISH) -> str:
        """Render a notification message"""
        template = self.get_template(template_type, language)
        
        if not template:
            logger.error(f"Template not found: {template_type.value}_{language.value}")
            return f"Notification: {variables.get('message', 'No message available')}"
        
        try:
            # Add urgency-related variables for bus arrival templates
            if template_type == TemplateType.BUS_ARRIVAL:
                eta_minutes = variables.get('eta_minutes', 0)
                if eta_minutes <= 2:
                    if language == Language.ENGLISH:
                        variables['urgency_suffix'] = " - Hurry! 🏃‍♂️"
                        variables['urgency_message'] = "\n\n⚡ *Arriving soon - Please be ready!*"
                    else:  # Kannada
                        variables['urgency_suffix'] = " - ಬೇಗ ಬನ್ನಿ! 🏃‍♂️"
                        variables['urgency_message'] = "\n\n⚡ *ಶೀಘ್ರದಲ್ಲೇ ಬರುತ್ತಿದೆ - ದಯವಿಟ್ಟು ಸಿದ್ಧವಾಗಿರಿ!*"
                else:
                    variables['urgency_suffix'] = ""
                    variables['urgency_message'] = ""
            
            return template.render(channel, variables)
            
        except Exception as e:
            logger.error(f"Failed to render notification: {str(e)}")
            return f"Notification error: {str(e)}"
    
    def get_available_templates(self) -> Dict[str, List[str]]:
        """Get list of available templates"""
        result = {}
        for template_type, languages in self.templates.items():
            result[template_type] = list(languages.keys())
        return result
    
    def validate_template_variables(self, template_type: TemplateType, 
                                  variables: Dict[str, Any],
                                  language: Language = Language.ENGLISH) -> List[str]:
        """Validate that all required variables are provided"""
        template = self.get_template(template_type, language)
        
        if not template:
            return [f"Template not found: {template_type.value}_{language.value}"]
        
        missing_variables = []
        for required_var in template.variables:
            if required_var not in variables:
                missing_variables.append(required_var)
        
        return missing_variables

# Global template manager instance
template_manager = NotificationTemplateManager()