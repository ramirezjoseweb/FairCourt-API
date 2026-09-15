import { useState } from "react";
import type { MeResponse } from "../api/me";
import { Button, Feedback, Icon, PageHeader } from "./ui";

export function ContactPanel({ me }: { me: MeResponse }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState(me.email);
  const [phone, setPhone] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");

  function submit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("Tu consulta se ha enviado correctamente.");
    setName("");
    setPhone("");
    setReason("");
  }

  function edit() {
    if (message) setMessage("");
  }

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="ESTAMOS PARA AYUDARTE"
        title="Hablemos."
        description="Envíanos tu consulta y el equipo de tu comunidad se pondrá en contacto contigo."
      />
      <div className="contact-layout">
        <section className="panel contact-panel" aria-labelledby="contact-title">
          <div className="contact-heading">
            <span className="empty-icon">
              <Icon name="mail" />
            </span>
            <div>
              <h2 id="contact-title">Cuéntanos en qué podemos ayudarte</h2>
              <p className="muted">
                Completa los datos de contacto y explica brevemente el motivo.
              </p>
            </div>
          </div>
          <Feedback message={message} />
          <form className="contact-form" onSubmit={submit} onInput={edit}>
            <div className="contact-field">
              <label htmlFor="contact-name">Nombre</label>
              <input
                id="contact-name"
                name="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Tu nombre y apellidos"
                autoComplete="name"
                maxLength={80}
                required
              />
            </div>
            <div className="contact-field">
              <label htmlFor="contact-email">E-mail</label>
              <input
                id="contact-email"
                name="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="tu@correo.es"
                autoComplete="email"
                maxLength={254}
                required
              />
            </div>
            <div className="contact-field contact-field-full">
              <label htmlFor="contact-phone">N.º de teléfono</label>
              <input
                id="contact-phone"
                name="phone"
                type="tel"
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="600 000 000"
                autoComplete="tel"
                inputMode="tel"
                maxLength={30}
                required
              />
            </div>
            <div className="contact-field contact-field-full">
              <label htmlFor="contact-reason">Motivo</label>
              <textarea
                id="contact-reason"
                name="reason"
                rows={6}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Describe brevemente tu consulta…"
                minLength={10}
                maxLength={1000}
                required
              />
              <span className="field-hint">Entre 10 y 1.000 caracteres.</span>
            </div>
            <Button type="submit" className="contact-submit">
              Enviar consulta
              <Icon name="arrow" />
            </Button>
          </form>
        </section>
        <aside className="contact-note" aria-label="Información de contacto">
          <p className="eyebrow">ATENCIÓN PERSONAL</p>
          <h2>Tu comunidad, más cerca.</h2>
          <p>
            Utiliza este formulario para dudas sobre reservas, instalaciones o
            cualquier incidencia que necesites comunicar.
          </p>
          <div className="contact-note-detail">
            <Icon name="clock" />
            <span>
              <strong>Respuesta del equipo</strong>
              Te responderemos a través del e-mail o teléfono indicados.
            </span>
          </div>
        </aside>
      </div>
    </div>
  );
}
