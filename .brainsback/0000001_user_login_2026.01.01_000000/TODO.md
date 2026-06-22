# Strategic Blueprint

> Focus on the **what** and **why**. The code will follow.

**Hard rule**: AI agents must not edit this file and must not draft paste-ready content for it.

## The Problem

Implementar autenticacao por email e senha com persistencia em banco. Con el objetivo de saber que usuario esta usando el sistema, se guarden sus conversaciones. Protegiendo los datos del usuario.

Requisitos minimos:

Cadastro/login por email e senha.
Logout funcional.
Dados de autenticacao persistidos no SQLite.

## Steps
- [ ] Creacion de las clases users con id, email, senha (encriptada con hash) archivo models.py
- [ ] Post api para guardar el nuevo usuario que recibe email y password (encriptada con hash)
- [ ] -Creacion del post api para logear , verificar las credenciales y devolver un token y validar la sesi´on
- [ ] Una funcion get_current_user para proteger rutas
- [ ] Un post api de logout para invalidar el token
- [ ] mostrar una ventana para mostrar la pantalla de login (segun el estado del token) y register para guardar/validar usuarios

## Success Looks Like
- [ ] Una ventana funcional que entrega un mensaje con contraseña equivocada cuando te equivoaues con la contraseña o si el email no existe.
- [ ] Al mismo tiempo que detecte emails repetidos
- [ ] Si te equivocas varias veces se bloquea ese mail por un tiempo (5 min en este caso al ser un eejemplo)

## Notes
- [ ] Recomendaciones: Librerías típicas a usar: python-jose o PyJWT — para generar/verificar JWT
- [ ] passlib[bcrypt] — para encriptar contraseñas (nunca guardes texto plano)
- [ ] fastapi.security — para HTTPBearer / OAuth2PasswordBearer
- [ ] las api en esta ruta backend/routers/auth.py
- [ ] la validadacion backend/schelas/auth.py
- [ ] backend/auth.py para get_current_user()
- [ ] Si hay faltas de ortografia/gramatic o logica intenta entender por tu cuenta, no seas 100% literal

---
**⚠️ HUMAN ONLY**: This file is your strategic space. AI agents must not edit it.
