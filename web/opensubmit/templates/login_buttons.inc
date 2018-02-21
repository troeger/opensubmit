{% load projecttags %}

{% setting "LOGIN_GOOGLE" as login_google %}
{% setting "LOGIN_OPENID" as login_openid %}
{% setting "LOGIN_TWITTER" as login_twitter %}
{% setting "LOGIN_GITHUB" as login_github %}
{% setting "LOGIN_DESCRIPTION" as login_description %}
{% setting "LOGIN_SHIB" as login_shib %}
{% setting "LOGIN_SHIB_DESCRIPTION" as login_shib_description %}
{% setting "DEMO" as demo %}

<section>
    <div class="row">
            <div class="col-md-2">
                Authentication with:
            </div>
            {% if login_google %}
                <div class="col-md-2">
                    <a href="{% url 'social:begin' 'google-oauth2' %}?next={{ request.path }}" class="btn-auth btn-google"><b>Google</b></a>
                </div>
            {% endif %}
            {% if login_twitter %}
                <div class="col-md-2">
                    <a href="{% url 'social:begin' 'twitter' %}?next={{ next }}" class="btn-auth btn-twitter"><b>Twitter</b></a>
                </div>
            {% endif %}
            {% if login_github %}
                <div class="col-md-2">
                    <a href="{% url 'social:begin' 'github' %}?next={{ next }}" class="btn-auth btn-github"><b>GitHub</b></a>
                </div>
            {% endif %}
            {% if login_openid %}
            <div class="col-md-3">
                <a href="{% url 'social:begin' 'openid' %}?next={{ next }}" class="btn-auth btn-openid"><b>{{ login_description }}</b></a>
            </div>
            {% endif %}
            {% if login_shib %}
            <div class="col-md-3">
                <a href="{% url 'social:begin' 'modshib' %}?next={{ next }}" class="btn-auth btn-openid"><b>{{ login_shib_description }}</b></a>
            </div>
            {% endif %}
    </div>
    {% if demo %}
    <br/>
    <div class="row">
            <div class="col-md-2">Anonymous login options for <b>demo mode</b>:</div>
            <div class="col-md-2">
                <a href="{% url 'demo' 'student' %}" class="btn-auth"><b>As student</b></a>
            </div>
            <div class="col-md-2">
                <a href="{% url 'demo' 'tutor' %}" class="btn-auth"><b>As course tutor</b></a>
            </div>
            <div class="col-md-2">
                <a href="{% url 'demo' 'owner' %}" class="btn-auth"><b>As course owner</b></a>
            </div>
            <div class="col-md-2">
                <a href="{% url 'demo' 'admin' %}" class="btn-auth"><b>As administrator</b></a>
            </div>
    </div>
    {% endif %}
</section>
