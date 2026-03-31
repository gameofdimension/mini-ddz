"""Tests for models.py"""

import torch
from models import DouZeroModel, model_dict


class TestModelDict:
    """Test model_dict."""

    def test_model_dict_exists(self):
        """Test that model_dict exists."""
        assert model_dict is not None
        assert isinstance(model_dict, dict)

    def test_model_dict_has_all_positions(self):
        """Test model_dict has all three positions."""
        assert len(model_dict) == 3
        expected_keys = {"landlord", "landlord_up", "landlord_down"}
        assert set(model_dict.keys()) == expected_keys

    def test_model_dict_values_are_callable(self):
        """Test that model_dict values are callable factories."""
        for key, factory in model_dict.items():
            assert callable(factory)
            instance = factory()
            assert isinstance(instance, DouZeroModel)


class TestLandlordModel:
    """Test landlord model (DouZeroModel with input_dim=373)."""

    def test_model_init(self):
        """Test model initialization."""
        model = model_dict["landlord"]()
        assert model is not None
        assert hasattr(model, "lstm")
        assert hasattr(model, "dense1")
        assert hasattr(model, "dense6")

    def test_model_forward(self):
        """Test model forward pass."""
        model = model_dict["landlord"]()
        model.eval()

        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 373)

        with torch.no_grad():
            output = model.forward(z, x)

        assert output.shape == (1, 1)

    def test_model_forward_batch(self):
        """Test model forward pass with batch size > 1."""
        model = model_dict["landlord"]()
        model.eval()

        batch_size = 4
        z = torch.randn(batch_size, 5, 162)
        x = torch.randn(batch_size, 373)

        with torch.no_grad():
            output = model.forward(z, x)

        assert output.shape == (batch_size, 1)


class TestFarmerModel:
    """Test farmer models (DouZeroModel with input_dim=484)."""

    def test_model_init(self):
        """Test model initialization."""
        model = model_dict["landlord_up"]()
        assert model is not None
        assert hasattr(model, "lstm")
        assert hasattr(model, "dense1")
        assert hasattr(model, "dense6")

    def test_model_forward(self):
        """Test model forward pass."""
        model = model_dict["landlord_up"]()
        model.eval()

        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 484)

        with torch.no_grad():
            output = model.forward(z, x)

        assert output.shape == (1, 1)

    def test_model_forward_batch(self):
        """Test model forward pass with batch size > 1."""
        model = model_dict["landlord_down"]()
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
        model = model_dict["landlord"]()
        model.eval()

        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 373)

        with torch.no_grad():
            output = model.forward(z, x)

        assert output.numel() == 1

    def test_farmer_output_range(self):
        """Test that farmer model output is in reasonable range."""
        model = model_dict["landlord_up"]()
        model.eval()

        z = torch.randn(1, 5, 162)
        x = torch.randn(1, 484)

        with torch.no_grad():
            output = model.forward(z, x)

        assert output.numel() == 1
