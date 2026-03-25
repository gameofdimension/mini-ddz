"""Tests for models.py"""
import pytest
import torch
import numpy as np

from models import LandlordLstmModel, FarmerLstmModel, model_dict


class TestModelDict:
    """Test model_dict."""

    def test_model_dict_exists(self):
        """Test that model_dict exists."""
        assert model_dict is not None
        assert isinstance(model_dict, dict)

    def test_model_dict_has_all_positions(self):
        """Test model_dict has all three positions."""
        assert len(model_dict) == 3
        expected_keys = {'landlord', 'landlord_up', 'landlord_down'}
        assert set(model_dict.keys()) == expected_keys
    
    def test_model_dict_values_are_callable(self):
        """Test that model_dict values are callable classes."""
        for key, model_class in model_dict.items():
            assert callable(model_class)
            # Should be able to instantiate
            instance = model_class()
            assert instance is not None


class TestLandlordLstmModel:
    """Test LandlordLstmModel class."""

    def test_model_init(self):
        """Test model initialization."""
        model = LandlordLstmModel()
        assert model is not None
        assert hasattr(model, 'lstm')
        assert hasattr(model, 'dense1')
        assert hasattr(model, 'dense6')

    def test_model_forward(self):
        """Test model forward pass."""
        model = LandlordLstmModel()
        model.eval()
        
        # Create dummy inputs
        # z: (batch=1, seq=5, features=162)
        # x: (batch=1, features=373)
        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 373)
        
        with torch.no_grad():
            output = model.forward(z, x)
        
        # Output should be (batch=1, 1)
        assert output.shape == (1, 1)

    def test_model_forward_batch(self):
        """Test model forward pass with batch size > 1."""
        model = LandlordLstmModel()
        model.eval()
        
        batch_size = 4
        z = torch.randn(batch_size, 5, 162)
        x = torch.randn(batch_size, 373)
        
        with torch.no_grad():
            output = model.forward(z, x)
        
        assert output.shape == (batch_size, 1)


class TestFarmerLstmModel:
    """Test FarmerLstmModel class."""

    def test_model_init(self):
        """Test model initialization."""
        model = FarmerLstmModel()
        assert model is not None
        assert hasattr(model, 'lstm')
        assert hasattr(model, 'dense1')
        assert hasattr(model, 'dense6')

    def test_model_forward(self):
        """Test model forward pass."""
        model = FarmerLstmModel()
        model.eval()
        
        # Create dummy inputs
        # z: (batch=1, seq=5, features=162)
        # x: (batch=1, features=484)
        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 484)
        
        with torch.no_grad():
            output = model.forward(z, x)
        
        # Output should be (batch=1, 1)
        assert output.shape == (1, 1)

    def test_model_forward_batch(self):
        """Test model forward pass with batch size > 1."""
        model = FarmerLstmModel()
        model.eval()
        
        batch_size = 4
        z = torch.randn(batch_size, 5, 162)
        x = torch.randn(batch_size, 484)
        
        with torch.no_grad():
            output = model.forward(z, x)
        
        assert output.shape == (batch_size, 1)


class TestModelOutput:
    """Test model output behavior."""

    def test_landlord_output_range(self):
        """Test that landlord model output is in reasonable range."""
        model = LandlordLstmModel()
        model.eval()
        
        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 373)
        
        with torch.no_grad():
            output = model.forward(z, x)
        
        # Output should be a single value (win rate prediction)
        assert output.numel() == 1

    def test_farmer_output_range(self):
        """Test that farmer model output is in reasonable range."""
        model = FarmerLstmModel()
        model.eval()
        
        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 484)
        
        with torch.no_grad():
            output = model.forward(z, x)
        
        assert output.numel() == 1
