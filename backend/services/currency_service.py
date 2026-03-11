"""Currency exchange service for international payments."""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional
import aiohttp
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Import will be added to models
# from models.database import ExchangeRate

logger = logging.getLogger(__name__)


class CurrencyService:
    """Service for handling currency conversion and exchange rates."""
    
    # Supported currencies (ISO 4217)
    SUPPORTED_CURRENCIES = [
        'USD', 'EUR', 'GBP', 'INR', 'AUD', 'CAD', 'SGD', 'AED',
        'JPY', 'CNY', 'BRL', 'MXN', 'ZAR', 'NZD', 'CHF', 'SEK',
        'NOK', 'DKK', 'PLN', 'THB', 'MYR', 'IDR', 'PHP', 'VND'
    ]
    
    BASE_CURRENCY = 'USD'
    
    def __init__(self, db: AsyncSession):
        """Initialize currency service with database session."""
        self.db = db
        self.api_key = os.getenv('CURRENCY_API_KEY', '')
        self.provider = os.getenv('CURRENCY_PROVIDER', 'manual')  # 'openexchangerates', 'currencyapi', 'manual'
        
    @classmethod
    def is_supported_currency(cls, currency: str) -> bool:
        """Check if currency is supported."""
        return currency.upper() in cls.SUPPORTED_CURRENCIES
    
    async def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        force_refresh: bool = False
    ) -> Optional[Decimal]:
        """
        Get exchange rate from one currency to another.
        
        Args:
            from_currency: Source currency code (ISO 4217)
            to_currency: Target currency code (ISO 4217)
            force_refresh: Force fetch from API even if cached
            
        Returns:
            Exchange rate as Decimal, or None if not available
        """
        if from_currency == to_currency:
            return Decimal('1.0')
        
        # Check both currencies are supported
        if not (self.is_supported_currency(from_currency) and self.is_supported_currency(to_currency)):
            logger.warning(f"Unsupported currency: {from_currency} or {to_currency}")
            return None
        
        # Try to get from database first (if not forcing refresh)
        if not force_refresh:
            rate = await self._get_cached_rate(from_currency, to_currency)
            if rate:
                return rate
        
        # Fetch from API if not cached or forcing refresh
        if self.provider != 'manual':
            await self._fetch_and_cache_rates()
            rate = await self._get_cached_rate(from_currency, to_currency)
            if rate:
                return rate
        
        # Fallback to manual rates if API fails
        return await self._get_manual_rate(from_currency, to_currency)
    
    async def _get_cached_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[Decimal]:
        """Get exchange rate from database cache."""
        try:
            from models.database import ExchangeRate
            
            # Check if rate is recent (less than 24 hours old)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            query = select(ExchangeRate).where(
                ExchangeRate.base_currency == from_currency,
                ExchangeRate.target_currency == to_currency,
                ExchangeRate.last_updated >= cutoff_time
            ).order_by(ExchangeRate.last_updated.desc())
            
            result = await self.db.execute(query)
            rate_obj = result.scalar_one_or_none()
            
            if rate_obj:
                logger.info(f"Using cached rate for {from_currency}/{to_currency}: {rate_obj.rate}")
                return Decimal(str(rate_obj.rate))
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching cached rate: {e}")
            return None
    
    async def _fetch_and_cache_rates(self) -> bool:
        """Fetch exchange rates from API and cache in database."""
        try:
            if self.provider == 'openexchangerates':
                return await self._fetch_from_openexchangerates()
            elif self.provider == 'currencyapi':
                return await self._fetch_from_currencyapi()
            else:
                logger.warning(f"Unknown provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error fetching exchange rates from API: {e}")
            return False
    
    async def _fetch_from_openexchangerates(self) -> bool:
        """Fetch rates from OpenExchangeRates API."""
        if not self.api_key:
            logger.warning("No API key configured for OpenExchangeRates")
            return False
        
        url = f"https://openexchangerates.org/api/latest.json?app_id={self.api_key}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get('rates', {})
                        
                        # Cache all rates
                        await self._cache_rates(self.BASE_CURRENCY, rates, 'openexchangerates')
                        logger.info(f"Fetched and cached {len(rates)} exchange rates")
                        return True
                    else:
                        logger.error(f"API returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error calling OpenExchangeRates API: {e}")
            return False
    
    async def _fetch_from_currencyapi(self) -> bool:
        """Fetch rates from CurrencyAPI."""
        if not self.api_key:
            logger.warning("No API key configured for CurrencyAPI")
            return False
        
        url = f"https://api.currencyapi.com/v3/latest?apikey={self.api_key}&base_currency={self.BASE_CURRENCY}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = {k: v['value'] for k, v in data.get('data', {}).items()}
                        
                        # Cache all rates
                        await self._cache_rates(self.BASE_CURRENCY, rates, 'currencyapi')
                        logger.info(f"Fetched and cached {len(rates)} exchange rates")
                        return True
                    else:
                        logger.error(f"API returned status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error calling CurrencyAPI: {e}")
            return False
    
    async def _cache_rates(
        self,
        base_currency: str,
        rates: Dict[str, float],
        provider: str
    ) -> None:
        """Cache exchange rates in database."""
        try:
            from models.database import ExchangeRate
            
            now = datetime.utcnow()
            
            for currency, rate in rates.items():
                if currency in self.SUPPORTED_CURRENCIES:
                    # Create or update rate
                    exchange_rate = ExchangeRate(
                        base_currency=base_currency,
                        target_currency=currency,
                        rate=Decimal(str(rate)),
                        provider=provider,
                        last_updated=now,
                        created_at=now
                    )
                    self.db.add(exchange_rate)
            
            await self.db.commit()
            logger.info(f"Cached rates from {provider}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error caching rates: {e}")
    
    async def _get_manual_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[Decimal]:
        """
        Get manual/fallback exchange rate.
        These are approximate rates and should be updated regularly.
        """
        # Approximate rates as of March 2026 (BASE: USD)
        manual_rates = {
            'USD': Decimal('1.0'),
            'EUR': Decimal('0.92'),
            'GBP': Decimal('0.79'),
            'INR': Decimal('83.50'),
            'AUD': Decimal('1.52'),
            'CAD': Decimal('1.36'),
            'SGD': Decimal('1.34'),
            'AED': Decimal('3.67'),
            'JPY': Decimal('149.50'),
            'CNY': Decimal('7.24'),
            'BRL': Decimal('5.02'),
            'MXN': Decimal('17.15'),
            'ZAR': Decimal('18.75'),
            'NZD': Decimal('1.65'),
            'CHF': Decimal('0.88'),
            'SEK': Decimal('10.45'),
            'NOK': Decimal('10.85'),
            'DKK': Decimal('6.87'),
            'PLN': Decimal('3.95'),
            'THB': Decimal('35.80'),
            'MYR': Decimal('4.72'),
            'IDR': Decimal('15850.00'),
            'PHP': Decimal('56.50'),
            'VND': Decimal('24750.00'),
        }
        
        if from_currency == 'USD':
            return manual_rates.get(to_currency)
        elif to_currency == 'USD':
            from_rate = manual_rates.get(from_currency)
            if from_rate and from_rate > 0:
                return Decimal('1.0') / from_rate
            return None
        else:
            # Convert via USD
            from_to_usd = manual_rates.get(from_currency)
            usd_to_target = manual_rates.get(to_currency)
            
            if from_to_usd and usd_to_target and from_to_usd > 0:
                return usd_to_target / from_to_usd
            return None
    
    async def convert_amount(
        self,
        amount: int,  # in smallest currency unit (paise, cents, etc.)
        from_currency: str,
        to_currency: str
    ) -> Optional[int]:
        """
        Convert amount from one currency to another.
        
        Args:
            amount: Amount in smallest unit (paise, cents)
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount in smallest unit, or None if conversion fails
        """
        rate = await self.get_exchange_rate(from_currency, to_currency)
        
        if rate is None:
            logger.error(f"Cannot convert {from_currency} to {to_currency}: no rate available")
            return None
        
        # Convert amount
        converted = Decimal(amount) * rate
        return int(converted.quantize(Decimal('1')))
    
    async def get_currency_display(
        self,
        amount: int,
        currency: str
    ) -> str:
        """
        Format amount for display with proper currency symbol.
        
        Args:
            amount: Amount in smallest unit
            currency: Currency code
            
        Returns:
            Formatted string (e.g., "$10.50", "₹100.00")
        """
        currency_symbols = {
            'USD': '$', 'EUR': '€', 'GBP': '£', 'INR': '₹',
            'AUD': 'A$', 'CAD': 'C$', 'SGD': 'S$', 'AED': 'د.إ',
            'JPY': '¥', 'CNY': '¥', 'BRL': 'R$', 'MXN': 'MX$',
            'ZAR': 'R', 'NZD': 'NZ$', 'CHF': 'CHF', 'SEK': 'kr',
            'NOK': 'kr', 'DKK': 'kr', 'PLN': 'zł', 'THB': '฿',
            'MYR': 'RM', 'IDR': 'Rp', 'PHP': '₱', 'VND': '₫'
        }
        
        symbol = currency_symbols.get(currency, currency)
        
        # Convert to major unit (divide by 100 for most currencies)
        if currency in ['JPY', 'VND', 'IDR']:  # Zero-decimal currencies
            major_amount = amount
        else:
            major_amount = amount / 100
        
        return f"{symbol}{major_amount:,.2f}"
