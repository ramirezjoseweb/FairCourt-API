type OfflineBannerProps = {
    isOnline: boolean;
};

/**
 * Banner visual que informa al usuario del estado de conexión.
 *
 * Si la aplicación está offline, muestra un aviso indicando que se están
 * usando datos almacenados localmente y que las acciones críticas requieren conexión.
 */
export function OfflineBanner({ isOnline }: OfflineBannerProps) {
    if (isOnline) {
        return null;
    }

    return (
        <div className="border-b border-amber-200 bg-amber-50 px-6 py-3 text-sm text-amber-800">
            <div className="mx-auto max-w-7xl">
                Estás sin conexión. Se mostrarán los últimos datos disponibles y las
                acciones como reservar, cancelar o hacer check-in requerirán conexión.
            </div>
        </div>
    );
}