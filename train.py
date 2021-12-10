import torch
from torch.utils import data
from tqdm import tqdm
from utils import stochastic_integral


def train(
    dataloader,
    model,
    criterion,
    optimizer,
    epochs,
    writer,
    scheduler=None,
    device="cpu",
    metric=None,
):
    num_batches = len(dataloader.dataset) / dataloader.batch_size
    model.train()
    for epoch in range(epochs):

        running_loss = 0

        with tqdm(enumerate(dataloader), unit="batch") as tepoch:
            for i, (x, x_inc, payoff, price) in tepoch:
                tepoch.set_description(f"Epoch {epoch}")

                x, x_inc, payoff, price = (
                    x.to(device),
                    x_inc.to(device),
                    payoff.to(device),
                    price.to(device),
                )

                optimizer.zero_grad()
                if not model.learn_price:
                    output = model(x)
                else:
                    output, price = model(x)
                si = stochastic_integral(x_inc, output)
                loss = criterion((price + si).float(), payoff.float())

                loss.backward()
                optimizer.step()

                if metric is not None:
                    tepoch.set_postfix(
                        {
                            "loss": loss.item(),
                            "metric": metric(price + si, payoff).item(),
                        }
                    )
                else:
                    tepoch.set_postfix(loss=loss.item())

                running_loss += loss.item()

        if scheduler is not None:
            scheduler.step()

        writer.add_scalar(
            "Average Loss in Epoch", running_loss / num_batches, epoch * num_batches
        )
        writer.close()


def test(data_loader, model, criterion, device="cpu"):
    model.eval_mode()

    x, x_inc, payoff, price = data_loader.dataset[:]
    x, x_inc, payoff, price = (
        x.to(device),
        x_inc.to(device),
        payoff.to(device),
        price.to(device),
    )

    if not model.learn_price:
        output = model(x)
    else:
        output, price = model(x)
    si = stochastic_integral(x_inc, output)
    loss = criterion(price + si, payoff)

    return output, price, loss


def train_dataset(
    dataset,
    model,
    criterion,
    optimizer,
    epochs,
    writer,
    scheduler=None,
    device="cpu",
    metric=None,
):

    model.train()
    for epoch in range(epochs):

        running_loss = 0

        with tqdm(range(dataset.splits), unit="batch") as tepoch:
            for i in tepoch:
                tepoch.set_description(f"Epoch {epoch}")

                x, x_inc, payoff, price = dataset[i]
                x, x_inc, payoff, price = (
                    x.to(device),
                    x_inc.to(device),
                    payoff.to(device),
                    price.to(device),
                )

                optimizer.zero_grad()
                if not model.learn_price:
                    output = model(x)
                else:
                    output, price = model(x)
                si = stochastic_integral(x_inc, output)
                loss = criterion((price + si).float(), payoff.float())

                loss.backward()
                optimizer.step()

                if metric is not None:
                    tepoch.set_postfix(
                        {
                            "loss": loss.item(),
                            "metric": metric(price + si, payoff).item(),
                        }
                    )
                else:
                    tepoch.set_postfix(loss=loss.item())

                running_loss += loss.item()

        if scheduler is not None:
            scheduler.step()

        writer.add_scalar(
            "Average Loss in Epoch",
            running_loss / dataset.splits,
            epoch * dataset.splits,
        )

        writer.close()
