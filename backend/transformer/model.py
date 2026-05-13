import torch
import torch.nn as nn


class AppTransformer(nn.Module):

    def __init__(
        self,
        vocab_size,
        embed_dim=64,
        num_heads=4,
        num_layers=2,
        num_classes=None,
        dropout=0.1,
        max_seq_len=10,
        context_dim=7
    ):

        super(AppTransformer, self).__init__()

        # =====================================================
        # APP EMBEDDINGS
        # =====================================================

        self.embedding = nn.Embedding(
            vocab_size,
            embed_dim,
            padding_idx=0
        )

        # =====================================================
        # POSITIONAL ENCODING
        # =====================================================

        self.pos_encoding = nn.Embedding(
            max_seq_len,
            embed_dim
        )

        # =====================================================
        # TRANSFORMER ENCODER
        # =====================================================

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dropout=dropout,
            batch_first=True
        )

        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        # =====================================================
        # CONTEXT FEATURES
        # =====================================================

        self.context_proj = nn.Linear(
            context_dim,
            embed_dim
        )

        # =====================================================
        # CLASSIFIER
        # =====================================================

        self.classifier = nn.Sequential(

            nn.Linear(
                embed_dim * 2,
                128
            ),

            nn.ReLU(),

            nn.Dropout(dropout),

            nn.Linear(
                128,
                num_classes
            )
        )

    def forward(
        self,
        token_seq,
        context_features
    ):

        batch_size, seq_len = token_seq.shape

        positions = (

            torch.arange(seq_len)

            .unsqueeze(0)

            .expand(batch_size, -1)

            .to(token_seq.device)
        )

        x = (

            self.embedding(token_seq)

            + self.pos_encoding(positions)
        )

        x = self.transformer_encoder(x)

        x = x.mean(dim=1)

        ctx = self.context_proj(
            context_features
        )

        combined = torch.cat(
            [x, ctx],
            dim=1
        )

        output = self.classifier(
            combined
        )

        return output


def get_topk_predictions(
    model,
    token_seq_tensor,
    context_tensor,
    k=3
):

    model.eval()

    with torch.no_grad():

        logits = model(
            token_seq_tensor,
            context_tensor
        )

        probs = torch.softmax(
            logits,
            dim=1
        )

        topk_probs, topk_indices = torch.topk(
            probs,
            k,
            dim=1
        )

    return (
        topk_indices[0].tolist(),
        topk_probs[0].tolist()
    )