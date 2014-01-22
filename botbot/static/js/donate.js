//
// Stripe
//
(function () {
    var handler = StripeCheckout.configure({
        key: 'pk_test_mQxyOcJvcRl1ryOuow2YvXW3',
        image: '/static/img/evil-logo-large-red.svg',
        panelLabel: 'Donate',
        token: function(token, args) {
            // Use the token to create the charge with a server-side script.
            $('.donate-form').hide();
            $('.donate-form-thanks').show();
        }
    });

    document.getElementById('donate-stripe').addEventListener('click', function(e) {
        var $stripeAmount = $('#donate-stripe-amount'),
            amount = parseFloat($stripeAmount.val()) * 100;

        if (isNaN(amount)) {
            $stripeAmount.addClass('error');
            return;
        } else {
            $stripeAmount.removeClass('error');
        }

        // Open Checkout with further options
        handler.open({
            name: 'BotBot',
            description: 'Donate to BotBot.me',
            amount: amount
        });
        e.preventDefault();
      });

})();